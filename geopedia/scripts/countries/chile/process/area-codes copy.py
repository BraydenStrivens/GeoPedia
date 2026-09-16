"""
Generate Chile fixed-line area-code polygons from validated OSM phone
observations using a Voronoi tessellation.

The telephone boundaries are inferred entirely from geographic phone
observations. Administrative boundaries do NOT determine area-code
boundaries.

Pipeline
--------
1. Read the OSM phone seed inspection.
2. Keep severity 0 and 1 observations.
3. Project Chile and the seeds into a metric CRS.
4. Generate Voronoi cells from all retained seeds.
5. Clip the Voronoi tessellation ONLY to Chile's national land geometry.
6. Assign each cell the area code of its generating seed.
7. Dissolve all cells belonging to the same area code.
8. Validate complete coverage of Chile.
9. Write the unsimplified canonical area-code geometry.
10. Temporarily also overwrite the runtime GeoJSON so the result can be
    inspected immediately in GeoPedia.

Inputs
------
data/intermediate/countries/chile/inspection/
    osm-phone-code-seed-inspection.geojson

data/intermediate/countries/chile/admin/regions.geojson

Outputs
-------
Canonical unsimplified:
data/intermediate/countries/chile/area-codes.geojson

Temporary runtime inspection output:
public/data/countries/chile/geojson/area-codes.geojson

Run with:

    python scripts/countries/chile/process/area-codes.py
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from pyproj import CRS, Transformer
from scipy.spatial import Voronoi
from shapely.geometry import (
    MultiPolygon,
    Polygon,
    mapping,
    shape,
)
from shapely.ops import (
    transform,
    unary_union,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]

SEEDS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "inspection"
    / "osm-phone-code-seed-inspection.geojson"
)

REGIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "admin"
    / "regions.geojson"
)

INTERMEDIATE_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "area-codes.geojson"
)

RUNTIME_OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "chile"
    / "geojson"
    / "area-codes.geojson"
)


# Keep both normal observations and possible real boundary observations.
MAX_SEED_SEVERITY = 1


EXPECTED_AREA_CODES = {
    "2",
    "32",
    "33",
    "34",
    "35",
    "41",
    "42",
    "43",
    "45",
    "51",
    "52",
    "53",
    "55",
    "57",
    "58",
    "61",
    "63",
    "64",
    "65",
    "67",
    "71",
    "72",
    "73",
    "75",
}


# EPSG:32719 = WGS 84 / UTM zone 19S.
#
# Chile spans multiple UTM zones, but zone 19S gives us a sensible metric
# coordinate system for constructing the tessellation. The final geometry
# is transformed back to WGS84.
PROJECTED_CRS = CRS.from_epsg(
    32719
)

WGS84_CRS = CRS.from_epsg(
    4326
)


def load_geojson(
    path: Path,
) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def make_transformers():
    to_projected_transformer = (
        Transformer.from_crs(
            WGS84_CRS,
            PROJECTED_CRS,
            always_xy=True,
        )
    )

    to_wgs84_transformer = (
        Transformer.from_crs(
            PROJECTED_CRS,
            WGS84_CRS,
            always_xy=True,
        )
    )

    return (
        to_projected_transformer,
        to_wgs84_transformer,
    )


def build_chile_geometry(
    regions_geojson: dict,
):
    geometries = []

    for feature in regions_geojson.get(
        "features",
        [],
    ):
        geometry_data = feature.get(
            "geometry"
        )

        if geometry_data is None:
            continue

        geometry = shape(
            geometry_data
        )

        if geometry.is_empty:
            continue

        geometries.append(
            geometry
        )

    if not geometries:
        raise ValueError(
            "No Chile region geometry found."
        )

    chile = unary_union(
        geometries
    )

    if not chile.is_valid:
        chile = chile.buffer(
            0
        )

    if chile.is_empty:
        raise ValueError(
            "Chile geometry is empty."
        )

    return chile


def load_seeds(
    seeds_geojson: dict,
) -> list[dict]:
    seeds = []

    counts = Counter()

    excluded_counts = Counter()

    for feature in seeds_geojson.get(
        "features",
        [],
    ):
        properties = feature.get(
            "properties",
            {},
        )

        area_code = str(
            properties.get(
                "area_code",
                "",
            )
        )

        if (
            area_code
            not in EXPECTED_AREA_CODES
        ):
            continue

        severity = int(
            properties.get(
                "seed_severity",
                0,
            )
        )

        if (
            severity
            > MAX_SEED_SEVERITY
        ):
            excluded_counts[
                area_code
            ] += 1

            continue

        geometry = feature.get(
            "geometry",
            {},
        )

        if geometry.get(
            "type"
        ) != "Point":
            continue

        coordinates = geometry.get(
            "coordinates"
        )

        if (
            not isinstance(
                coordinates,
                list,
            )
            or len(coordinates) < 2
        ):
            continue

        lon = float(
            coordinates[0]
        )

        lat = float(
            coordinates[1]
        )

        seeds.append(
            {
                "lon": lon,
                "lat": lat,
                "area_code": area_code,
                "severity": severity,
            }
        )

        counts[
            area_code
        ] += 1

    missing_codes = (
        EXPECTED_AREA_CODES
        - set(counts)
    )

    if missing_codes:
        raise ValueError(
            "No retained seeds for area codes: "
            + ", ".join(
                sorted(
                    missing_codes
                )
            )
        )

    print()
    print("RETAINED SEEDS")
    print("=" * 70)

    for area_code in sorted(
        EXPECTED_AREA_CODES,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        print(
            f"{area_code:>2} -> "
            f"kept {counts[area_code]:>4} | "
            f"excluded "
            f"{excluded_counts[area_code]:>3}"
        )

    print()
    print(
        f"Total retained: "
        f"{len(seeds)}"
    )

    print(
        f"Total excluded: "
        f"{sum(excluded_counts.values())}"
    )

    return seeds


def deduplicate_seed_locations(
    seeds: list[dict],
) -> list[dict]:
    """
    SciPy Voronoi cannot use duplicate coordinate pairs reliably.

    If multiple observations occur at exactly the same coordinates and
    agree on the area code, collapse them into one seed.

    If multiple DIFFERENT area codes occur at exactly the same
    coordinates, choose the locally most represented code at that
    coordinate and report the conflict.

    Exact coordinate conflicts should be rare after seed filtering.
    """

    by_coordinate = defaultdict(
        list
    )

    for seed in seeds:
        key = (
            seed["lon"],
            seed["lat"],
        )

        by_coordinate[
            key
        ].append(
            seed
        )

    deduplicated = []

    duplicate_locations = 0
    conflicting_locations = 0

    for (
        coordinates,
        group,
    ) in by_coordinate.items():
        if len(group) > 1:
            duplicate_locations += 1

        counts = Counter(
            seed["area_code"]
            for seed in group
        )

        if len(counts) > 1:
            conflicting_locations += 1

            print()
            print(
                "WARNING: conflicting codes at "
                f"{coordinates}: "
                f"{dict(counts)}"
            )

        area_code = max(
            counts.items(),
            key=lambda item: (
                item[1],
                item[0],
            ),
        )[0]

        deduplicated.append(
            {
                "lon": coordinates[0],
                "lat": coordinates[1],
                "area_code": area_code,
            }
        )

    print()
    print("SEED LOCATION DEDUPLICATION")
    print("=" * 70)

    print(
        f"Input seeds:             "
        f"{len(seeds)}"
    )

    print(
        f"Unique seed locations:   "
        f"{len(deduplicated)}"
    )

    print(
        f"Duplicate locations:     "
        f"{duplicate_locations}"
    )

    print(
        f"Conflicting locations:   "
        f"{conflicting_locations}"
    )

    return deduplicated


def voronoi_finite_polygons_2d(
    voronoi: Voronoi,
    radius: float | None = None,
):
    """
    Reconstruct infinite SciPy Voronoi regions into finite polygons.

    Adapted from the standard SciPy Voronoi finite-region reconstruction
    approach.
    """

    if voronoi.points.shape[1] != 2:
        raise ValueError(
            "Voronoi input must be 2D."
        )

    new_regions = []

    new_vertices = (
        voronoi.vertices.tolist()
    )

    center = (
        voronoi.points.mean(
            axis=0
        )
    )

    if radius is None:
        radius = (
            np.ptp(
                voronoi.points,
                axis=0,
            ).max()
            * 4
        )

    all_ridges = defaultdict(
        list
    )

    for (
        point_1,
        point_2,
    ), (
        vertex_1,
        vertex_2,
    ) in zip(
        voronoi.ridge_points,
        voronoi.ridge_vertices,
    ):
        all_ridges[
            point_1
        ].append(
            (
                point_2,
                vertex_1,
                vertex_2,
            )
        )

        all_ridges[
            point_2
        ].append(
            (
                point_1,
                vertex_1,
                vertex_2,
            )
        )

    for (
        point_index,
        region_index,
    ) in enumerate(
        voronoi.point_region
    ):
        vertices = (
            voronoi.regions[
                region_index
            ]
        )

        if all(
            vertex >= 0
            for vertex in vertices
        ):
            new_regions.append(
                vertices
            )

            continue

        ridges = all_ridges[
            point_index
        ]

        new_region = [
            vertex
            for vertex in vertices
            if vertex >= 0
        ]

        for (
            other_point_index,
            vertex_1,
            vertex_2,
        ) in ridges:
            if (
                vertex_2 < 0
                and vertex_1 >= 0
            ):
                vertex_1, vertex_2 = (
                    vertex_2,
                    vertex_1,
                )

            if vertex_1 >= 0:
                continue

            tangent = (
                voronoi.points[
                    other_point_index
                ]
                - voronoi.points[
                    point_index
                ]
            )

            tangent /= np.linalg.norm(
                tangent
            )

            normal = np.array(
                [
                    -tangent[1],
                    tangent[0],
                ]
            )

            midpoint = (
                voronoi.points[
                    [
                        point_index,
                        other_point_index,
                    ]
                ].mean(
                    axis=0
                )
            )

            direction = np.sign(
                np.dot(
                    midpoint - center,
                    normal,
                )
            ) * normal

            far_point = (
                voronoi.vertices[
                    vertex_2
                ]
                + direction
                * radius
            )

            new_region.append(
                len(
                    new_vertices
                )
            )

            new_vertices.append(
                far_point.tolist()
            )

        region_vertices = np.asarray(
            [
                new_vertices[
                    vertex
                ]
                for vertex
                in new_region
            ]
        )

        centroid = (
            region_vertices.mean(
                axis=0
            )
        )

        angles = np.arctan2(
            region_vertices[
                :,
                1,
            ]
            - centroid[1],
            region_vertices[
                :,
                0,
            ]
            - centroid[0],
        )

        new_region = np.array(
            new_region
        )[
            np.argsort(
                angles
            )
        ]

        new_regions.append(
            new_region.tolist()
        )

    return (
        new_regions,
        np.asarray(
            new_vertices
        ),
    )


def generate_voronoi_cells(
    seeds: list[dict],
    chile_projected,
    to_projected_transformer: Transformer,
) -> dict[str, list]:
    projected_points = []

    for seed in seeds:
        x, y = (
            to_projected_transformer
            .transform(
                seed["lon"],
                seed["lat"],
            )
        )

        projected_points.append(
            (
                x,
                y,
            )
        )

    point_array = np.asarray(
        projected_points
    )

    print()
    print("GENERATING VORONOI")
    print("=" * 70)

    print(
        f"Voronoi seed locations: "
        f"{len(point_array)}"
    )

    voronoi = Voronoi(
        point_array
    )

    (
        regions,
        vertices,
    ) = (
        voronoi_finite_polygons_2d(
            voronoi
        )
    )

    by_area_code = defaultdict(
        list
    )

    nonempty_cells = 0

    for (
        seed,
        region,
    ) in zip(
        seeds,
        regions,
    ):
        polygon = Polygon(
            vertices[
                region
            ]
        )

        if not polygon.is_valid:
            polygon = polygon.buffer(
                0
            )

        if polygon.is_empty:
            continue

        clipped = polygon.intersection(
            chile_projected
        )

        if clipped.is_empty:
            continue

        by_area_code[
            seed["area_code"]
        ].append(
            clipped
        )

        nonempty_cells += 1

    print(
        f"Non-empty clipped cells: "
        f"{nonempty_cells}"
    )

    return by_area_code


def dissolve_area_codes(
    by_area_code: dict[str, list],
) -> dict[str, object]:
    dissolved = {}

    print()
    print("DISSOLVING AREA CODES")
    print("=" * 70)

    for area_code in sorted(
        EXPECTED_AREA_CODES,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        geometries = (
            by_area_code.get(
                area_code,
                [],
            )
        )

        if not geometries:
            raise ValueError(
                f"Area code {area_code} "
                "has no Voronoi cells."
            )

        geometry = unary_union(
            geometries
        )

        if not geometry.is_valid:
            geometry = geometry.buffer(
                0
            )

        if geometry.is_empty:
            raise ValueError(
                f"Area code {area_code} "
                "dissolved to empty geometry."
            )

        dissolved[
            area_code
        ] = geometry

        print(
            f"{area_code:>2} -> "
            f"{len(geometries):>4} cells"
        )

    return dissolved


def validate_coverage(
    chile_projected,
    dissolved: dict[str, object],
) -> None:
    print()
    print("COVERAGE VALIDATION")
    print("=" * 70)

    area_code_union = unary_union(
        list(
            dissolved.values()
        )
    )

    chile_area = (
        chile_projected.area
    )

    union_area = (
        area_code_union.area
    )

    missing_geometry = (
        chile_projected.difference(
            area_code_union
        )
    )

    outside_geometry = (
        area_code_union.difference(
            chile_projected
        )
    )

    missing_area = (
        missing_geometry.area
    )

    outside_area = (
        outside_geometry.area
    )

    summed_area = sum(
        geometry.area
        for geometry
        in dissolved.values()
    )

    overlap_area = max(
        0.0,
        summed_area - union_area,
    )

    coverage_percent = (
        union_area
        / chile_area
        * 100
        if chile_area
        else 0
    )

    missing_percent = (
        missing_area
        / chile_area
        * 100
        if chile_area
        else 0
    )

    overlap_percent = (
        overlap_area
        / chile_area
        * 100
        if chile_area
        else 0
    )

    print(
        f"Chile area:        "
        f"{chile_area / 1_000_000:,.2f} km²"
    )

    print(
        f"Voronoi union:     "
        f"{union_area / 1_000_000:,.2f} km²"
    )

    print(
        f"Coverage:          "
        f"{coverage_percent:.10f}%"
    )

    print(
        f"Missing:           "
        f"{missing_area / 1_000_000:.8f} km² "
        f"({missing_percent:.12f}%)"
    )

    print(
        f"Outside Chile:     "
        f"{outside_area / 1_000_000:.8f} km²"
    )

    print(
        f"Overlap:           "
        f"{overlap_area / 1_000_000:.8f} km² "
        f"({overlap_percent:.12f}%)"
    )

    # Numerical geometry operations can leave microscopic floating-point
    # differences. Allow one square meter relative to the projected
    # national geometry.
    tolerance_square_meters = 1.0

    if (
        missing_area
        > tolerance_square_meters
    ):
        raise ValueError(
            "Voronoi coverage validation failed: "
            f"{missing_area:.6f} m² of Chile "
            "is uncovered."
        )

    if (
        outside_area
        > tolerance_square_meters
    ):
        raise ValueError(
            "Voronoi coverage validation failed: "
            f"{outside_area:.6f} m² lies "
            "outside Chile."
        )

    if (
        overlap_area
        > tolerance_square_meters
    ):
        raise ValueError(
            "Voronoi coverage validation failed: "
            f"{overlap_area:.6f} m² overlaps."
        )

    print()
    print(
        "Coverage validation passed."
    )


def normalize_polygon_geometry(
    geometry,
):
    """
    Keep polygonal components only.
    """

    if geometry.geom_type in {
        "Polygon",
        "MultiPolygon",
    }:
        return geometry

    polygons = []

    if hasattr(
        geometry,
        "geoms",
    ):
        for part in geometry.geoms:
            if part.geom_type == "Polygon":
                polygons.append(
                    part
                )

            elif (
                part.geom_type
                == "MultiPolygon"
            ):
                polygons.extend(
                    list(
                        part.geoms
                    )
                )

    if not polygons:
        raise ValueError(
            "Geometry contains no polygonal parts."
        )

    if len(polygons) == 1:
        return polygons[0]

    return MultiPolygon(
        polygons
    )


def build_output_geojson(
    dissolved: dict[str, object],
    to_wgs84_transformer: Transformer,
) -> dict:
    features = []

    for area_code in sorted(
        EXPECTED_AREA_CODES,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        projected_geometry = (
            dissolved[
                area_code
            ]
        )

        wgs84_geometry = transform(
            to_wgs84_transformer.transform,
            projected_geometry,
        )

        wgs84_geometry = (
            normalize_polygon_geometry(
                wgs84_geometry
            )
        )

        if not wgs84_geometry.is_valid:
            wgs84_geometry = (
                wgs84_geometry.buffer(
                    0
                )
            )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "area_code_id": (
                        area_code
                    ),
                    "area_code": (
                        area_code
                    ),
                },
                "geometry": mapping(
                    wgs84_geometry
                ),
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def write_geojson(
    geojson: dict,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            geojson,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def main() -> None:
    print()
    print(
        "CHILE AREA-CODE VORONOI"
    )
    print("=" * 70)

    seeds_geojson = load_geojson(
        SEEDS_PATH
    )

    regions_geojson = load_geojson(
        REGIONS_PATH
    )

    (
        to_projected_transformer,
        to_wgs84_transformer,
    ) = make_transformers()

    chile_wgs84 = (
        build_chile_geometry(
            regions_geojson
        )
    )

    chile_projected = transform(
        to_projected_transformer.transform,
        chile_wgs84,
    )

    if not chile_projected.is_valid:
        chile_projected = (
            chile_projected.buffer(
                0
            )
        )

    seeds = load_seeds(
        seeds_geojson
    )

    seeds = (
        deduplicate_seed_locations(
            seeds
        )
    )

    by_area_code = (
        generate_voronoi_cells(
            seeds,
            chile_projected,
            to_projected_transformer,
        )
    )

    dissolved = (
        dissolve_area_codes(
            by_area_code
        )
    )

    validate_coverage(
        chile_projected,
        dissolved,
    )

    output_geojson = (
        build_output_geojson(
            dissolved,
            to_wgs84_transformer,
        )
    )

    if (
        len(
            output_geojson[
                "features"
            ]
        )
        != len(
            EXPECTED_AREA_CODES
        )
    ):
        raise ValueError(
            "Expected "
            f"{len(EXPECTED_AREA_CODES)} "
            "output features."
        )

    write_geojson(
        output_geojson,
        INTERMEDIATE_OUTPUT_PATH,
    )

    write_geojson(
        output_geojson,
        RUNTIME_OUTPUT_PATH,
    )

    intermediate_size_mb = (
        INTERMEDIATE_OUTPUT_PATH
        .stat()
        .st_size
        / 1024
        / 1024
    )

    runtime_size_mb = (
        RUNTIME_OUTPUT_PATH
        .stat()
        .st_size
        / 1024
        / 1024
    )

    print()
    print("OUTPUT")
    print("=" * 70)

    print(
        f"Features: "
        f"{len(output_geojson['features'])}"
    )

    print(
        f"Intermediate size: "
        f"{intermediate_size_mb:.2f} MB"
    )

    print(
        f"Runtime size:      "
        f"{runtime_size_mb:.2f} MB"
    )

    print()
    print(
        f"Saved canonical: "
        f"{INTERMEDIATE_OUTPUT_PATH}"
    )

    print(
        f"Overwrote runtime: "
        f"{RUNTIME_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()