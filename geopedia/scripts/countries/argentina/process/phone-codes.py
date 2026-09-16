from __future__ import annotations

import json
import math
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from pyproj import CRS, Transformer
from scipy.spatial import QhullError, Voronoi
from shapely import make_valid, union_all
from shapely.geometry import (
    GeometryCollection,
    MultiPolygon,
    Point,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import nearest_points, transform as shapely_transform


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SEEDS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "countries"
    / "argentina"
    / "phone-code-localities.geojson"
)

PROVINCES_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "argentina"
    / "provinces.geojson"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "countries"
    / "argentina"
)

FULL_OUTPUT_PATH = OUTPUT_DIR / "phone-codes-full.geojson"
THREE_DIGIT_OUTPUT_PATH = OUTPUT_DIR / "phone-codes-3-digit.geojson"
TWO_DIGIT_OUTPUT_PATH = OUTPUT_DIR / "phone-codes-2-digit.geojson"
ONE_DIGIT_OUTPUT_PATH = OUTPUT_DIR / "phone-codes-1-digit.geojson"


# Seeds closer than this after rounding are treated as the same
# coordinate. Eight decimal places in WGS84 is far finer than this
# approximate telephone-region dataset needs.
COORDINATE_ROUNDING = 8

# A few official locality points can sit just outside the administrative
# boundary because the two source datasets were produced independently.
# Those points are snapped to the nearest point on Argentina's boundary,
# but anything farther away than this is treated as suspicious.
MAX_NEAREST_COUNTRY_DISTANCE_DEGREES = 0.25

# Eight guard points are placed well outside Argentina so every real
# locality receives a finite scipy Voronoi region before clipping.
GUARD_MARGIN_MULTIPLIER = 10.0

# If numerical clipping/reprojection leaves a tiny uncovered sliver, it
# can be assigned to the neighboring Voronoi cell that shares the most
# boundary with it. Larger gaps indicate a genuine construction problem.
MAX_REPAIRABLE_GAP_RELATIVE = 1e-4  # 0.01%

# Final coverage should still be essentially complete. This tolerance is
# intentionally much stricter than the overlap tolerance.
COVERAGE_RELATIVE_TOLERANCE = 1e-8

# GeoPedia already tolerates small overlaps in simplified quiz geometry.
# 0.001 as a ratio is 0.1% of Argentina's area. Anything larger is likely
# a real geometry bug rather than harmless numerical/simplification noise.
OVERLAP_RELATIVE_TOLERANCE = 1e-3  # 0.1%


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )
    return " ".join(value.upper().strip().split())


def load_geojson(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_geojson(
    path: Path,
    feature_collection: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            feature_collection,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )


def polygonal_only(geometry: Any) -> Polygon | MultiPolygon:
    """Return only polygonal parts of a Shapely geometry."""
    if geometry is None or geometry.is_empty:
        return Polygon()

    if isinstance(geometry, (Polygon, MultiPolygon)):
        return geometry

    if isinstance(geometry, GeometryCollection):
        polygon_parts = [
            part
            for part in geometry.geoms
            if isinstance(part, (Polygon, MultiPolygon))
            and not part.is_empty
        ]

        if not polygon_parts:
            return Polygon()

        return polygonal_only(union_all(polygon_parts))

    return Polygon()


def clean_polygonal(geometry: Any) -> Polygon | MultiPolygon:
    if geometry is None or geometry.is_empty:
        return Polygon()

    if not geometry.is_valid:
        geometry = make_valid(geometry)

    geometry = polygonal_only(geometry)

    if not geometry.is_empty and not geometry.is_valid:
        geometry = polygonal_only(make_valid(geometry))

    return geometry


def load_provinces() -> list[dict[str, Any]]:
    data = load_geojson(PROVINCES_PATH)
    provinces: list[dict[str, Any]] = []

    for index, feature in enumerate(data["features"]):
        properties = feature.get("properties", {})

        province_id = str(
            properties.get("province_id")
            or f"province-{index}"
        )
        province_name = str(
            properties.get("province")
            or province_id
        )

        geometry = clean_polygonal(shape(feature["geometry"]))

        if geometry.is_empty:
            raise RuntimeError(
                f"Province has empty geometry: {province_name}"
            )

        provinces.append(
            {
                "id": province_id,
                "name": province_name,
                "name_normalized": normalize_text(province_name),
                "geometry": geometry,
            }
        )

    return provinces


def build_country_geometry(
    provinces: list[dict[str, Any]],
) -> Polygon | MultiPolygon:
    country = clean_polygonal(
        union_all(
            [
                province["geometry"]
                for province in provinces
            ]
        )
    )

    if country.is_empty:
        raise RuntimeError(
            "Argentina province union produced an empty country geometry."
        )

    return country


def load_seed_features() -> list[dict[str, Any]]:
    data = load_geojson(SEEDS_PATH)
    seeds: list[dict[str, Any]] = []

    for index, feature in enumerate(data["features"]):
        properties = feature.get("properties", {})

        area_code = str(
            properties.get("area_code") or ""
        ).strip()

        if not area_code:
            raise RuntimeError(
                f"Seed feature {index} has no area_code."
            )

        geometry = shape(feature["geometry"])

        if not isinstance(geometry, Point):
            raise RuntimeError(
                f"Seed feature {index} is not a Point."
            )

        province_hint = str(
            properties.get("official_province")
            or properties.get("province")
            or properties.get("source_province")
            or ""
        ).strip()

        locality = str(
            properties.get("official_locality")
            or properties.get("locality")
            or properties.get("source_locality")
            or ""
        ).strip()

        seeds.append(
            {
                "index": index,
                "area_code": area_code,
                "point": geometry,
                "province_hint": province_hint,
                "locality": locality,
                "properties": properties,
            }
        )

    return seeds


def prepare_country_seeds(
    seeds: list[dict[str, Any]],
    country_geometry: Polygon | MultiPolygon,
) -> tuple[list[dict[str, Any]], int]:
    """
    Snap the rare slightly-outside source points to Argentina, then
    deduplicate coordinates globally.

    Different full area codes are never allowed to share one coordinate.
    That must be resolved in phone-code-localities.py, where the source
    evidence is available.
    """
    snapped_rows: list[tuple[float, dict[str, Any], Point]] = []
    prepared: list[dict[str, Any]] = []

    for seed in seeds:
        point: Point = seed["point"]
        working_point = point

        if not country_geometry.covers(point):
            country_point, _ = nearest_points(
                country_geometry,
                point,
            )
            distance = point.distance(country_point)

            if distance > MAX_NEAREST_COUNTRY_DISTANCE_DEGREES:
                raise RuntimeError(
                    "Seed is too far outside Argentina:\n"
                    f"  area code: {seed['area_code']}\n"
                    f"  locality: {seed['locality']}\n"
                    f"  province hint: {seed['province_hint']}\n"
                    f"  coordinate: {point.y:.6f}, {point.x:.6f}\n"
                    f"  nearest-country distance: {distance:.6f} degrees"
                )

            working_point = country_point
            snapped_rows.append((distance, seed, country_point))

        prepared_seed = dict(seed)
        prepared_seed["working_point"] = working_point
        prepared.append(prepared_seed)

    if snapped_rows:
        snapped_rows.sort(key=lambda row: row[0], reverse=True)
        print()
        print("Seeds snapped to Argentina instead of contained:")

        for distance, seed, snapped_point in snapped_rows[:20]:
            original: Point = seed["point"]
            print(
                f"  {seed['area_code']} | "
                f"{seed['locality']} | "
                f"{original.y:.5f}, {original.x:.5f} -> "
                f"{snapped_point.y:.5f}, {snapped_point.x:.5f} | "
                f"{distance:.6f}°"
            )

    groups: dict[
        tuple[float, float],
        list[dict[str, Any]],
    ] = defaultdict(list)

    for seed in prepared:
        point: Point = seed["working_point"]
        key = (
            round(point.x, COORDINATE_ROUNDING),
            round(point.y, COORDINATE_ROUNDING),
        )
        groups[key].append(seed)

    deduplicated: list[dict[str, Any]] = []
    duplicate_count = 0
    conflicts: list[
        tuple[
            tuple[float, float],
            list[dict[str, Any]],
        ]
    ] = []

    for coordinate, group in groups.items():
        codes = {seed["area_code"] for seed in group}

        if len(codes) == 1:
            deduplicated.append(group[0])
            duplicate_count += len(group) - 1
            continue

        conflicts.append((coordinate, group))

    if conflicts:
        print()
        print("=" * 80)
        print("CONFLICTING DUPLICATE SEED COORDINATES")
        print("=" * 80)
        print(f"Conflicting coordinates: {len(conflicts):,}")

        for coordinate, group in conflicts[:30]:
            print()
            print(
                f"  {coordinate[1]:.8f}, "
                f"{coordinate[0]:.8f}"
            )
            for seed in group:
                print(
                    f"    code {seed['area_code']} | "
                    f"{seed['locality']} | "
                    f"{seed['province_hint']}"
                )

        raise RuntimeError(
            "The same coordinate is assigned to multiple area codes. "
            "Resolve these seed conflicts in the locality-matching stage "
            "before building Voronoi polygons."
        )

    return deduplicated, duplicate_count


def make_country_transformers(
    country_geometry: Polygon | MultiPolygon,
) -> tuple[Transformer, Transformer]:
    """
    Use one azimuthal-equidistant projection centered on Argentina.

    The phone-code boundaries are approximate nearest-locality regions,
    so one consistent national metric projection is preferable to 24
    independent province projections with artificial hard walls.
    """
    centroid = country_geometry.centroid

    local_crs = CRS.from_proj4(
        "+proj=aeqd "
        f"+lat_0={centroid.y} "
        f"+lon_0={centroid.x} "
        "+datum=WGS84 "
        "+units=m "
        "+no_defs"
    )

    forward = Transformer.from_crs(
        "EPSG:4326",
        local_crs,
        always_xy=True,
    )
    backward = Transformer.from_crs(
        local_crs,
        "EPSG:4326",
        always_xy=True,
    )

    return forward, backward


def add_guard_points(
    coordinates: np.ndarray,
    bounds: tuple[float, float, float, float],
) -> np.ndarray:
    min_x, min_y, max_x, max_y = bounds

    width = max_x - min_x
    height = max_y - min_y
    scale = max(width, height, 1.0)
    margin = scale * GUARD_MARGIN_MULTIPLIER

    left = min_x - margin
    right = max_x + margin
    bottom = min_y - margin
    top = max_y + margin
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0

    guards = np.array(
        [
            [left, bottom],
            [left, top],
            [right, bottom],
            [right, top],
            [center_x, bottom],
            [center_x, top],
            [left, center_y],
            [right, center_y],
        ],
        dtype=float,
    )

    return np.vstack([coordinates, guards])


def run_voronoi(points: np.ndarray) -> Voronoi:
    try:
        return Voronoi(points)
    except QhullError:
        # QJ perturbs degenerate / nearly collinear coordinates very
        # slightly and is used only if normal Qhull cannot solve them.
        return Voronoi(
            points,
            qhull_options="Qbb Qc Qz QJ",
        )


def project_point(
    point: Point,
    transformer: Transformer,
) -> Point:
    x, y = transformer.transform(point.x, point.y)
    return Point(x, y)


def polygon_parts(
    geometry: Polygon | MultiPolygon,
) -> list[Polygon]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    return [part for part in geometry.geoms if not part.is_empty]


def repair_partition_gaps(
    cells: list[dict[str, Any]],
    country_geometry: Polygon | MultiPolygon,
) -> float:
    """
    Repair only tiny numerical gaps in the projected national partition.

    The gap is assigned to the cell with which it shares the longest
    boundary. Distance is used only as a tie-breaker.
    """
    cells_union = clean_polygonal(
        union_all([cell["geometry"] for cell in cells])
    )
    uncovered = clean_polygonal(
        country_geometry.difference(cells_union)
    )

    if uncovered.is_empty:
        return 0.0

    relative_uncovered = uncovered.area / max(
        country_geometry.area,
        1e-30,
    )

    if relative_uncovered > MAX_REPAIRABLE_GAP_RELATIVE:
        raise RuntimeError(
            "National Voronoi cells leave a suspiciously large gap.\n"
            f"Relative uncovered area: {relative_uncovered:.12%}"
        )

    for gap in polygon_parts(uncovered):
        best_index: int | None = None
        best_shared_boundary = -1.0
        best_distance = math.inf

        for index, cell in enumerate(cells):
            cell_geometry = cell["geometry"]
            shared_boundary = (
                cell_geometry.boundary
                .intersection(gap.boundary)
                .length
            )
            distance = cell_geometry.distance(gap)

            if (
                shared_boundary > best_shared_boundary
                or (
                    math.isclose(
                        shared_boundary,
                        best_shared_boundary,
                    )
                    and distance < best_distance
                )
            ):
                best_index = index
                best_shared_boundary = shared_boundary
                best_distance = distance

        if best_index is None:
            raise RuntimeError(
                "Could not assign a national Voronoi coverage gap."
            )

        cells[best_index]["geometry"] = clean_polygonal(
            union_all(
                [
                    cells[best_index]["geometry"],
                    gap,
                ]
            )
        )

    repaired_union = clean_polygonal(
        union_all([cell["geometry"] for cell in cells])
    )
    remaining_uncovered = country_geometry.difference(repaired_union)
    remaining_relative = remaining_uncovered.area / max(
        country_geometry.area,
        1e-30,
    )

    if remaining_relative > 1e-10:
        raise RuntimeError(
            "National Voronoi gap repair did not fully cover Argentina.\n"
            f"Remaining relative uncovered area: "
            f"{remaining_relative:.12%}"
        )

    return relative_uncovered


def validate_projected_partition(
    cells: list[dict[str, Any]],
    projected_country: Polygon | MultiPolygon,
) -> None:
    invalid_count = sum(
        1
        for cell in cells
        if not cell["geometry"].is_valid
    )
    empty_count = sum(
        1
        for cell in cells
        if cell["geometry"].is_empty
    )

    cell_geometries = [cell["geometry"] for cell in cells]
    cells_union = clean_polygonal(union_all(cell_geometries))

    country_area = projected_country.area
    union_area = cells_union.area
    individual_area = sum(
        geometry.area
        for geometry in cell_geometries
    )

    coverage_difference = (
        projected_country.symmetric_difference(cells_union).area
    )
    overlap_area = max(0.0, individual_area - union_area)

    coverage_relative = coverage_difference / max(country_area, 1.0)
    overlap_relative = overlap_area / max(country_area, 1.0)

    print()
    print("Raw national Voronoi partition validation:")
    print(f"  cells: {len(cells):,}")
    print(f"  invalid cells: {invalid_count:,}")
    print(f"  empty cells: {empty_count:,}")
    print(f"  coverage difference: {coverage_relative:.12%}")
    print(f"  overlap: {overlap_relative:.12%}")

    if invalid_count:
        raise RuntimeError(
            "Raw national Voronoi partition contains invalid cells."
        )

    if empty_count:
        raise RuntimeError(
            "Raw national Voronoi partition contains empty cells."
        )

    if coverage_relative > COVERAGE_RELATIVE_TOLERANCE:
        raise RuntimeError(
            "Raw national Voronoi partition does not cover Argentina "
            "closely enough."
        )

    if overlap_relative > OVERLAP_RELATIVE_TOLERANCE:
        raise RuntimeError(
            "Raw national Voronoi partition contains too much overlap."
        )


def build_country_voronoi_cells(
    seeds: list[dict[str, Any]],
    country_geometry: Polygon | MultiPolygon,
) -> list[tuple[str, Polygon | MultiPolygon]]:
    forward, backward = make_country_transformers(country_geometry)

    projected_country = clean_polygonal(
        shapely_transform(
            forward.transform,
            country_geometry,
        )
    )

    projected_points = [
        project_point(
            seed["working_point"],
            forward,
        )
        for seed in seeds
    ]

    # Defensive check after projection. Exact duplicate projected points
    # would make Qhull unstable even if the source coordinates differed
    # only below our normal WGS84 rounding precision.
    projected_groups: dict[
        tuple[float, float],
        list[int],
    ] = defaultdict(list)

    for index, point in enumerate(projected_points):
        projected_groups[
            (
                round(point.x, 6),
                round(point.y, 6),
            )
        ].append(index)

    projected_conflicts = [
        indexes
        for indexes in projected_groups.values()
        if len(indexes) > 1
    ]

    if projected_conflicts:
        rows = []
        for indexes in projected_conflicts[:20]:
            codes = {seeds[index]["area_code"] for index in indexes}
            rows.append(
                ", ".join(
                    f"{seeds[index]['area_code']} "
                    f"({seeds[index]['locality']})"
                    for index in indexes
                )
            )

        raise RuntimeError(
            "Multiple seeds collapsed to the same projected coordinate. "
            "Resolve before Voronoi construction:\n  "
            + "\n  ".join(rows)
        )

    coordinate_array = np.array(
        [[point.x, point.y] for point in projected_points],
        dtype=float,
    )

    all_points = add_guard_points(
        coordinate_array,
        projected_country.bounds,
    )

    voronoi = run_voronoi(all_points)

    projected_cells: list[dict[str, Any]] = []
    missing_regions = 0

    for seed_index, seed in enumerate(seeds):
        region_index = voronoi.point_region[seed_index]
        vertex_indexes = voronoi.regions[region_index]

        if not vertex_indexes or -1 in vertex_indexes:
            missing_regions += 1
            continue

        vertices = [
            voronoi.vertices[vertex_index]
            for vertex_index in vertex_indexes
        ]

        cell = clean_polygonal(Polygon(vertices))
        cell = clean_polygonal(
            cell.intersection(projected_country)
        )

        if cell.is_empty:
            raise RuntimeError(
                "A real phone-code seed produced an empty national "
                "Voronoi cell:\n"
                f"  code: {seed['area_code']}\n"
                f"  locality: {seed['locality']}\n"
                f"  province: {seed['province_hint']}"
            )

        projected_cells.append(
            {
                "area_code": seed["area_code"],
                "geometry": cell,
            }
        )

    if missing_regions:
        raise RuntimeError(
            f"National Voronoi produced {missing_regions} infinite or "
            "missing real-seed regions despite guard points."
        )

    repaired_relative = repair_partition_gaps(
        projected_cells,
        projected_country,
    )

    if repaired_relative > 0.0:
        print(
            "  repaired national coverage gap: "
            f"{repaired_relative:.12%}"
        )

    validate_projected_partition(
        projected_cells,
        projected_country,
    )

    wgs84_cells: list[
        tuple[str, Polygon | MultiPolygon]
    ] = []

    for cell in projected_cells:
        geometry = clean_polygonal(
            shapely_transform(
                backward.transform,
                cell["geometry"],
            )
        )

        if geometry.is_empty:
            raise RuntimeError(
                f"Area code {cell['area_code']} transformed to "
                "empty WGS84 geometry."
            )

        # Re-clip after inverse projection so every output point remains
        # inside the exact WGS84 Argentina boundary.
        geometry = clean_polygonal(
            geometry.intersection(country_geometry)
        )

        wgs84_cells.append(
            (cell["area_code"], geometry)
        )

    return wgs84_cells


def dissolve_cells_by_full_code(
    cells: list[tuple[str, Polygon | MultiPolygon]],
) -> dict[str, Polygon | MultiPolygon]:
    by_code: dict[
        str,
        list[Polygon | MultiPolygon],
    ] = defaultdict(list)

    for area_code, geometry in cells:
        by_code[area_code].append(geometry)

    dissolved: dict[str, Polygon | MultiPolygon] = {}

    for area_code, geometries in by_code.items():
        geometry = clean_polygonal(union_all(geometries))

        if geometry.is_empty:
            raise RuntimeError(
                f"Area code {area_code} dissolved to empty geometry."
            )

        dissolved[area_code] = geometry

    return dissolved


def prefix_for_depth(area_code: str, depth: int) -> str:
    if len(area_code) <= depth:
        return area_code
    return area_code[:depth]


def dissolve_to_depth(
    full_geometries: dict[str, Polygon | MultiPolygon],
    depth: int,
) -> dict[str, Polygon | MultiPolygon]:
    grouped: dict[
        str,
        list[Polygon | MultiPolygon],
    ] = defaultdict(list)

    for area_code, geometry in full_geometries.items():
        grouped[
            prefix_for_depth(area_code, depth)
        ].append(geometry)

    return {
        prefix: clean_polygonal(union_all(geometries))
        for prefix, geometries in grouped.items()
    }


def code_sort_key(value: str) -> tuple[int | float, str]:
    try:
        return int(value), value
    except ValueError:
        return math.inf, value


def seed_counts_by_code(
    seeds: list[dict[str, Any]],
) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)

    for seed in seeds:
        counts[seed["area_code"]] += 1

    return counts


def make_feature_collection(
    geometries: dict[str, Polygon | MultiPolygon],
    level: str,
    seed_counts: dict[str, int],
    source_full_codes: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    features: list[dict[str, Any]] = []

    for area_code in sorted(geometries, key=code_sort_key):
        geometry = clean_polygonal(geometries[area_code])

        if geometry.is_empty:
            continue

        properties: dict[str, Any] = {
            "area_code": area_code,
            "level": level,
        }

        if level in {
            "2-digit",
            "3-digit",
            "full",
        }:
            properties["phone_code_1_digit"] = prefix_for_depth(
                area_code,
                1,
            )

        if level in {
            "3-digit",
            "full",
        }:
            properties["phone_code_2_digit"] = prefix_for_depth(
                area_code,
                2,
            )

        if level == "full":
            properties["phone_code_3_digit"] = prefix_for_depth(
                area_code,
                3,
            )

        if level == "full":
            properties["area_code_length"] = len(area_code)
            properties["seed_count"] = seed_counts.get(area_code, 0)
        else:
            full_codes = (
                source_full_codes.get(area_code, set())
                if source_full_codes
                else set()
            )
            properties["source_code_count"] = len(full_codes)
            properties["seed_count"] = sum(
                seed_counts.get(full_code, 0)
                for full_code in full_codes
            )

        features.append(
            {
                "type": "Feature",
                "id": area_code,
                "properties": properties,
                "geometry": mapping(geometry),
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def source_codes_for_depth(
    full_codes: list[str],
    depth: int,
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)

    for full_code in full_codes:
        result[
            prefix_for_depth(full_code, depth)
        ].add(full_code)

    return result


def equal_area_geometry(geometry: Any) -> Any:
    transformer = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:6933",
        always_xy=True,
    )
    return shapely_transform(
        transformer.transform,
        geometry,
    )


def validate_dataset(
    label: str,
    geometries: dict[str, Polygon | MultiPolygon],
    expected_country: Polygon | MultiPolygon,
) -> None:
    invalid_codes = [
        code
        for code, geometry in geometries.items()
        if not geometry.is_valid
    ]

    empty_codes = [
        code
        for code, geometry in geometries.items()
        if geometry.is_empty
    ]

    output_union = clean_polygonal(
        union_all(list(geometries.values()))
    )

    # Do topology operations while everything is still in the
    # original WGS84 coordinate space. Reprojecting neighboring
    # polygons independently can introduce microscopic differences
    # along shared edges, which can cause GEOS topology exceptions.
    coverage_difference = clean_polygonal(
        expected_country.symmetric_difference(
            output_union
        )
    )

    # EPSG:6933 is used only for measuring area, not for topology.
    expected_equal_area = equal_area_geometry(
        expected_country
    )

    union_equal_area = equal_area_geometry(
        output_union
    )

    difference_equal_area = equal_area_geometry(
        coverage_difference
    )

    expected_area = expected_equal_area.area
    union_area = union_equal_area.area
    missing_or_extra_area = difference_equal_area.area

    individual_area = sum(
        equal_area_geometry(
            geometry
        ).area
        for geometry in geometries.values()
    )

    overlap_area = max(
        0.0,
        individual_area - union_area,
    )

    coverage_relative = (
        missing_or_extra_area
        / max(expected_area, 1.0)
    )

    overlap_relative = (
        overlap_area
        / max(expected_area, 1.0)
    )

    print()
    print(
        f"{label} validation:"
    )

    print(
        f"  features: "
        f"{len(geometries):,}"
    )

    print(
        f"  invalid geometries: "
        f"{len(invalid_codes):,}"
    )

    print(
        f"  empty geometries: "
        f"{len(empty_codes):,}"
    )

    print(
        f"  expected area: "
        f"{expected_area / 1_000_000:,.2f} km²"
    )

    print(
        f"  union area: "
        f"{union_area / 1_000_000:,.2f} km²"
    )

    print(
        "  coverage difference: "
        f"{missing_or_extra_area / 1_000_000:,.6f} km² "
        f"({coverage_relative:.12%})"
    )

    print(
        "  overlap area: "
        f"{overlap_area / 1_000_000:,.6f} km² "
        f"({overlap_relative:.12%})"
    )

    if invalid_codes:
        print(
            "  invalid codes: "
            + ", ".join(
                invalid_codes[:20]
            )
        )

        raise RuntimeError(
            f"{label} contains invalid geometries."
        )

    if empty_codes:
        print(
            "  empty codes: "
            + ", ".join(
                empty_codes[:20]
            )
        )

        raise RuntimeError(
            f"{label} contains empty geometries."
        )

    if (
        coverage_relative
        > COVERAGE_RELATIVE_TOLERANCE
    ):
        raise RuntimeError(
            f"{label} does not match "
            f"Argentina coverage closely enough."
        )

    if (
        overlap_relative
        > OVERLAP_RELATIVE_TOLERANCE
    ):
        raise RuntimeError(
            f"{label} contains too much "
            f"overlapping area-code geometry."
        )

def main() -> None:
    print("Loading Argentina phone-code Voronoi inputs...")

    provinces = load_provinces()
    country_geometry = build_country_geometry(provinces)
    raw_seeds = load_seed_features()

    print()
    print(f"Provinces used to build country border: {len(provinces):,}")
    print(f"Input seed points: {len(raw_seeds):,}")

    distinct_input_codes = {
        seed["area_code"]
        for seed in raw_seeds
    }
    print(f"Distinct input area codes: {len(distinct_input_codes):,}")

    seeds, duplicate_seed_count = prepare_country_seeds(
        raw_seeds,
        country_geometry,
    )

    print()
    print(
        "Duplicate same-code seed coordinates removed: "
        f"{duplicate_seed_count:,}"
    )
    print(f"Seeds used for national Voronoi: {len(seeds):,}")

    print()
    print("=" * 80)
    print("BUILDING NATIONAL VORONOI CELLS")
    print("=" * 80)

    cells = build_country_voronoi_cells(
        seeds,
        country_geometry,
    )

    print()
    print(f"Total national Voronoi cells: {len(cells):,}")

    print()
    print("Dissolving cells by full area code...")

    full_geometries = dissolve_cells_by_full_code(cells)

    if set(full_geometries) != distinct_input_codes:
        missing_codes = distinct_input_codes - set(full_geometries)
        extra_codes = set(full_geometries) - distinct_input_codes
        raise RuntimeError(
            "Full-code output does not preserve all input codes.\n"
            f"Missing: {sorted(missing_codes)}\n"
            f"Extra: {sorted(extra_codes)}"
        )

    three_digit = dissolve_to_depth(full_geometries, 3)
    two_digit = dissolve_to_depth(full_geometries, 2)
    one_digit = dissolve_to_depth(full_geometries, 1)

    validate_dataset(
        "Full-code",
        full_geometries,
        country_geometry,
    )
    validate_dataset(
        "3-digit",
        three_digit,
        country_geometry,
    )
    validate_dataset(
        "2-digit",
        two_digit,
        country_geometry,
    )
    validate_dataset(
        "1-digit",
        one_digit,
        country_geometry,
    )

    counts = seed_counts_by_code(seeds)
    full_codes = list(full_geometries)

    three_sources = source_codes_for_depth(full_codes, 3)
    two_sources = source_codes_for_depth(full_codes, 2)
    one_sources = source_codes_for_depth(full_codes, 1)

    full_collection = make_feature_collection(
        full_geometries,
        "full",
        counts,
    )
    three_collection = make_feature_collection(
        three_digit,
        "3-digit",
        counts,
        three_sources,
    )
    two_collection = make_feature_collection(
        two_digit,
        "2-digit",
        counts,
        two_sources,
    )
    one_collection = make_feature_collection(
        one_digit,
        "1-digit",
        counts,
        one_sources,
    )

    write_geojson(FULL_OUTPUT_PATH, full_collection)
    write_geojson(THREE_DIGIT_OUTPUT_PATH, three_collection)
    write_geojson(TWO_DIGIT_OUTPUT_PATH, two_collection)
    write_geojson(ONE_DIGIT_OUTPUT_PATH, one_collection)

    print()
    print("=" * 80)
    print("ARGENTINA PHONE-CODE POLYGONS COMPLETE")
    print("=" * 80)
    print(f"Full codes: {len(full_geometries):,}")
    print(f"3-digit values: {len(three_digit):,}")
    print(f"2-digit values: {len(two_digit):,}")
    print(f"1-digit values: {len(one_digit):,}")

    print()
    print("Wrote:")
    print(f"  {FULL_OUTPUT_PATH}")
    print(f"  {THREE_DIGIT_OUTPUT_PATH}")
    print(f"  {TWO_DIGIT_OUTPUT_PATH}")
    print(f"  {ONE_DIGIT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()