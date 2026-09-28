"""
Generate Chile fixed-line area-code polygons from validated OSM phone
observations using a Voronoi tessellation.

Telephone boundaries are inferred from geographic phone observations.
Administrative boundaries do NOT determine area-code boundaries.

Special handling is applied to area code 2 because OSM contains many
Santiago telephone numbers attached to chain businesses and organizations
elsewhere in Chile.

Pipeline
--------
1. Read validated OSM phone observations.
2. Keep severity 0 and 1 observations.
3. Filter area-code 2 observations to the geographically connected
   Santiago population.
4. Deduplicate exact seed locations.
5. Build a simplified Chile national land mask.
6. Generate a Voronoi tessellation from retained observations.
7. Clip Voronoi cells ONLY to the Chile national land mask.
8. Dissolve cells by area code.
9. Validate complete coverage of the processed Chile mask.
10. Write canonical intermediate and temporary runtime GeoJSON.

Inputs
------
data/intermediate/countries/chile/inspection/
    osm-phone-code-seed-inspection.geojson

data/intermediate/countries/chile/admin/regions.geojson

Outputs
-------
data/intermediate/countries/chile/area-codes.geojson

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
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import transform, unary_union
from sklearn.cluster import DBSCAN


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


# ---------------------------------------------------------------------------
# Area-code 2 filtering
# ---------------------------------------------------------------------------
#
# Stage 1:
# Find the enormous dense Santiago cluster using a conservative 5 km DBSCAN.
#
# Stage 2:
# Keep additional code-2 observations that can connect back to that population
# through a larger 20 km neighborhood.
#
# This preserves legitimate satellite populations around Santiago while
# preventing isolated code-2 clusters in places such as Concepción, Temuco,
# Antofagasta, etc. from participating in the Voronoi.
#
# The second stage is intentionally implemented as graph connectivity from
# the Santiago core rather than simply running DBSCAN at 20 km over the whole
# country.

CODE_2_CORE_RADIUS_KM = 5.0
CODE_2_CONNECTION_RADIUS_KM = 20.0
CODE_2_MIN_SAMPLES = 3

EARTH_RADIUS_KM = 6371.0088


# ---------------------------------------------------------------------------
# Country mask
# ---------------------------------------------------------------------------
#
# The source Chile geometry is much more detailed than a quiz map needs.
#
# We simplify the NATIONAL mask before clipping thousands of Voronoi cells.
# This should dramatically reduce processing time and output size.
#
# EPSG:32719 is metric, so these values are meters / square meters.

COASTLINE_SIMPLIFY_METERS = 500.0

# Remove disconnected polygon pieces smaller than 1 km².
#
# This removes the huge number of tiny rocks/islets that add geometry without
# being useful quiz targets, while retaining substantial islands.
MIN_LAND_AREA_SQ_KM = 1.0


WGS84_CRS = CRS.from_epsg(4326)

PROJECTED_CRS = CRS.from_epsg(32719)


def load_geojson(path: Path) -> dict:
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
    to_projected_transformer = Transformer.from_crs(
        WGS84_CRS,
        PROJECTED_CRS,
        always_xy=True,
    )

    to_wgs84_transformer = Transformer.from_crs(
        PROJECTED_CRS,
        WGS84_CRS,
        always_xy=True,
    )

    return (
        to_projected_transformer,
        to_wgs84_transformer,
    )


def extract_polygons(geometry) -> list[Polygon]:
    if geometry.is_empty:
        return []

    if geometry.geom_type == "Polygon":
        return [geometry]

    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)

    polygons = []

    if hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            polygons.extend(
                extract_polygons(part)
            )

    return polygons


def polygon_vertex_count(geometry) -> int:
    count = 0

    for polygon in extract_polygons(
        geometry
    ):
        count += len(
            polygon.exterior.coords
        )

        for interior in polygon.interiors:
            count += len(
                interior.coords
            )

    return count


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
        chile = chile.buffer(0)

    if chile.is_empty:
        raise ValueError(
            "Chile geometry is empty."
        )

    return chile


def build_quiz_land_mask(
    chile_projected,
):
    print()
    print("BUILDING QUIZ LAND MASK")
    print("=" * 70)

    original_polygons = extract_polygons(
        chile_projected
    )

    original_area = chile_projected.area

    original_vertices = polygon_vertex_count(
        chile_projected
    )

    minimum_area = (
        MIN_LAND_AREA_SQ_KM
        * 1_000_000
    )

    kept_polygons = []
    removed_polygons = []

    for polygon in original_polygons:
        if polygon.area >= minimum_area:
            kept_polygons.append(
                polygon
            )
        else:
            removed_polygons.append(
                polygon
            )

    if not kept_polygons:
        raise ValueError(
            "Island filtering removed all Chile geometry."
        )

    filtered = unary_union(
        kept_polygons
    )

    if not filtered.is_valid:
        filtered = filtered.buffer(0)

    filtered_area = filtered.area

    filtered_vertices = polygon_vertex_count(
        filtered
    )

    simplified = filtered.simplify(
        COASTLINE_SIMPLIFY_METERS,
        preserve_topology=True,
    )

    if not simplified.is_valid:
        simplified = simplified.buffer(0)

    if simplified.is_empty:
        raise ValueError(
            "Simplified Chile geometry is empty."
        )

    simplified_vertices = (
        polygon_vertex_count(
            simplified
        )
    )

    simplified_area = simplified.area

    removed_area = (
        original_area
        - filtered_area
    )

    simplification_area_change = (
        simplified_area
        - filtered_area
    )

    print(
        f"Original polygon parts: "
        f"{len(original_polygons)}"
    )

    print(
        f"Kept polygon parts:     "
        f"{len(kept_polygons)}"
    )

    print(
        f"Removed tiny parts:     "
        f"{len(removed_polygons)}"
    )

    print(
        f"Minimum island area:    "
        f"{MIN_LAND_AREA_SQ_KM:.2f} km²"
    )

    print()

    print(
        f"Original vertices:      "
        f"{original_vertices:,}"
    )

    print(
        f"After island filter:    "
        f"{filtered_vertices:,}"
    )

    print(
        f"After simplification:   "
        f"{simplified_vertices:,}"
    )

    print()

    print(
        f"Original area:          "
        f"{original_area / 1_000_000:,.2f} km²"
    )

    print(
        f"Removed island area:    "
        f"{removed_area / 1_000_000:,.4f} km²"
    )

    print(
        f"Simplification change:  "
        f"{simplification_area_change / 1_000_000:,.4f} km²"
    )

    print(
        f"Final mask area:        "
        f"{simplified_area / 1_000_000:,.2f} km²"
    )

    return simplified


def load_candidate_seeds(
    seeds_geojson: dict,
) -> list[dict]:
    seeds = []

    original_counts = Counter()
    severity_excluded_counts = Counter()

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

        if area_code not in EXPECTED_AREA_CODES:
            continue

        original_counts[
            area_code
        ] += 1

        severity = int(
            properties.get(
                "seed_severity",
                0,
            )
        )

        if severity > MAX_SEED_SEVERITY:
            severity_excluded_counts[
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

        seeds.append(
            {
                "lon": float(
                    coordinates[0]
                ),
                "lat": float(
                    coordinates[1]
                ),
                "area_code": area_code,
                "severity": severity,
            }
        )

    print()
    print("SEVERITY FILTER")
    print("=" * 70)

    for area_code in sorted(
        EXPECTED_AREA_CODES,
        key=lambda value: (
            len(value),
            value,
        ),
    ):
        retained = (
            original_counts[area_code]
            - severity_excluded_counts[
                area_code
            ]
        )

        print(
            f"{area_code:>2} -> "
            f"kept {retained:>4} | "
            f"excluded "
            f"{severity_excluded_counts[area_code]:>3}"
        )

    print()
    print(
        f"After severity filter: "
        f"{len(seeds)}"
    )

    return seeds


def haversine_coordinate_array(
    seeds: list[dict],
) -> np.ndarray:
    return np.radians(
        np.asarray(
            [
                [
                    seed["lat"],
                    seed["lon"],
                ]
                for seed in seeds
            ],
            dtype=float,
        )
    )


def find_code_2_core(
    code_2_seeds: list[dict],
) -> set[int]:
    coordinates = (
        haversine_coordinate_array(
            code_2_seeds
        )
    )

    epsilon = (
        CODE_2_CORE_RADIUS_KM
        / EARTH_RADIUS_KM
    )

    model = DBSCAN(
        eps=epsilon,
        min_samples=CODE_2_MIN_SAMPLES,
        metric="haversine",
        algorithm="ball_tree",
    )

    labels = model.fit_predict(
        coordinates
    )

    cluster_counts = Counter(
        int(label)
        for label in labels
        if label != -1
    )

    if not cluster_counts:
        raise ValueError(
            "No area-code 2 DBSCAN clusters found."
        )

    largest_cluster_label = (
        cluster_counts.most_common(1)[0][0]
    )

    return {
        index
        for index, label
        in enumerate(labels)
        if int(label)
        == largest_cluster_label
    }


def haversine_distances_from(
    coordinate_radians: np.ndarray,
    all_coordinates_radians: np.ndarray,
) -> np.ndarray:
    lat_1 = coordinate_radians[0]
    lon_1 = coordinate_radians[1]

    lat_2 = all_coordinates_radians[
        :,
        0
    ]

    lon_2 = all_coordinates_radians[
        :,
        1
    ]

    delta_lat = lat_2 - lat_1
    delta_lon = lon_2 - lon_1

    a = (
        np.sin(
            delta_lat / 2.0
        )
        ** 2
        + np.cos(lat_1)
        * np.cos(lat_2)
        * np.sin(
            delta_lon / 2.0
        )
        ** 2
    )

    c = 2.0 * np.arctan2(
        np.sqrt(a),
        np.sqrt(
            np.maximum(
                0.0,
                1.0 - a,
            )
        ),
    )

    return (
        EARTH_RADIUS_KM
        * c
    )


def expand_code_2_population(
    code_2_seeds: list[dict],
    core_indices: set[int],
) -> set[int]:
    """
    Expand outward from the dense Santiago core.

    A candidate joins the accepted population if it is within
    CODE_2_CONNECTION_RADIUS_KM of ANY already accepted observation.

    Expansion repeats until no more observations can connect.

    This is effectively a geographic connected component anchored to the
    known Santiago core.
    """

    coordinates = (
        haversine_coordinate_array(
            code_2_seeds
        )
    )

    accepted = set(
        core_indices
    )

    frontier = set(
        core_indices
    )

    unaccepted = (
        set(
            range(
                len(code_2_seeds)
            )
        )
        - accepted
    )

    while frontier:
        new_frontier = set()

        # Working only against currently unaccepted observations keeps the
        # operation small enough for ~2,100 code-2 points.
        unaccepted_list = list(
            unaccepted
        )

        if not unaccepted_list:
            break

        unaccepted_coordinates = (
            coordinates[
                unaccepted_list
            ]
        )

        for accepted_index in frontier:
            distances = (
                haversine_distances_from(
                    coordinates[
                        accepted_index
                    ],
                    unaccepted_coordinates,
                )
            )

            nearby_positions = np.where(
                distances
                <= CODE_2_CONNECTION_RADIUS_KM
            )[0]

            for position in nearby_positions:
                new_frontier.add(
                    unaccepted_list[
                        int(position)
                    ]
                )

        if not new_frontier:
            break

        accepted.update(
            new_frontier
        )

        unaccepted.difference_update(
            new_frontier
        )

        frontier = new_frontier

    return accepted


def filter_code_2_seeds(
    seeds: list[dict],
) -> list[dict]:
    code_2_seeds = [
        seed
        for seed in seeds
        if seed["area_code"] == "2"
    ]

    other_seeds = [
        seed
        for seed in seeds
        if seed["area_code"] != "2"
    ]

    print()
    print("AREA CODE 2 FILTER")
    print("=" * 70)

    print(
        f"Candidate code-2 seeds: "
        f"{len(code_2_seeds)}"
    )

    core_indices = find_code_2_core(
        code_2_seeds
    )

    print(
        f"5 km Santiago core:     "
        f"{len(core_indices)}"
    )

    accepted_indices = (
        expand_code_2_population(
            code_2_seeds,
            core_indices,
        )
    )

    accepted_code_2 = [
        seed
        for index, seed
        in enumerate(code_2_seeds)
        if index in accepted_indices
    ]

    rejected_code_2 = [
        seed
        for index, seed
        in enumerate(code_2_seeds)
        if index not in accepted_indices
    ]

    print(
        f"After 20 km expansion:  "
        f"{len(accepted_code_2)}"
    )

    print(
        f"Rejected code-2 seeds:  "
        f"{len(rejected_code_2)}"
    )

    if accepted_code_2:
        lons = [
            seed["lon"]
            for seed in accepted_code_2
        ]

        lats = [
            seed["lat"]
            for seed in accepted_code_2
        ]

        print(
            "Accepted bounds:        "
            f"lon {min(lons):.5f} "
            f"to {max(lons):.5f}, "
            f"lat {min(lats):.5f} "
            f"to {max(lats):.5f}"
        )

    if rejected_code_2:
        print()
        print(
            "Sample rejected code-2 observations:"
        )

        # Print geographic extremes so obvious nationwide contamination is
        # visible in the console without producing hundreds of lines.
        rejected_sorted = sorted(
            rejected_code_2,
            key=lambda seed: seed["lat"],
            reverse=True,
        )

        sample = []

        sample.extend(
            rejected_sorted[:5]
        )

        sample.extend(
            rejected_sorted[-5:]
        )

        seen = set()

        for seed in sample:
            key = (
                seed["lon"],
                seed["lat"],
            )

            if key in seen:
                continue

            seen.add(key)

            print(
                f"  ({seed['lon']:.5f}, "
                f"{seed['lat']:.5f})"
            )

    return (
        other_seeds
        + accepted_code_2
    )


def validate_retained_codes(
    seeds: list[dict],
) -> None:
    counts = Counter(
        seed["area_code"]
        for seed in seeds
    )

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
    print("FINAL SEED COUNTS")
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
            f"{counts[area_code]:>4}"
        )

    print()
    print(
        f"Total retained seeds: "
        f"{len(seeds)}"
    )


def deduplicate_seed_locations(
    seeds: list[dict],
) -> list[dict]:
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

    for coordinates, group in (
        by_coordinate.items()
    ):
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

        # If several observations at one exact coordinate agree, collapse
        # them. If they disagree, use the locally most represented code.
        #
        # A tie is deterministic but is also printed above for inspection.
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
    if voronoi.points.shape[1] != 2:
        raise ValueError(
            "Voronoi input must be 2D."
        )

    new_regions = []

    new_vertices = (
        voronoi.vertices.tolist()
    )

    center = voronoi.points.mean(
        axis=0
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
                len(new_vertices)
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

        centroid = region_vertices.mean(
            axis=0
        )

        angles = np.arctan2(
            region_vertices[:, 1]
            - centroid[1],
            region_vertices[:, 0]
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
            to_projected_transformer.transform(
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

    regions, vertices = (
        voronoi_finite_polygons_2d(
            voronoi
        )
    )

    by_area_code = defaultdict(
        list
    )

    nonempty_cells = 0

    for seed, region in zip(
        seeds,
        regions,
    ):
        polygon = Polygon(
            vertices[
                region
            ]
        )

        if not polygon.is_valid:
            polygon = polygon.buffer(0)

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
            geometry = geometry.buffer(0)

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

    print(
        f"Processed Chile area: "
        f"{chile_area / 1_000_000:,.2f} km²"
    )

    print(
        f"Voronoi union:        "
        f"{union_area / 1_000_000:,.2f} km²"
    )

    print(
        f"Coverage:             "
        f"{coverage_percent:.10f}%"
    )

    print(
        f"Missing:              "
        f"{missing_area / 1_000_000:.8f} km²"
    )

    print(
        f"Outside Chile:        "
        f"{outside_area / 1_000_000:.8f} km²"
    )

    print(
        f"Overlap:              "
        f"{overlap_area / 1_000_000:.8f} km²"
    )

    tolerance_square_meters = 1.0

    if (
        missing_area
        > tolerance_square_meters
    ):
        raise ValueError(
            "Voronoi coverage validation failed: "
            f"{missing_area:.6f} m² "
            "is uncovered."
        )

    if (
        outside_area
        > tolerance_square_meters
    ):
        raise ValueError(
            "Voronoi coverage validation failed: "
            f"{outside_area:.6f} m² "
            "lies outside Chile."
        )

    if (
        overlap_area
        > tolerance_square_meters
    ):
        raise ValueError(
            "Voronoi coverage validation failed: "
            f"{overlap_area:.6f} m² "
            "overlaps."
        )

    print()
    print(
        "Coverage validation passed."
    )


def normalize_polygon_geometry(
    geometry,
):
    polygons = extract_polygons(
        geometry
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
                wgs84_geometry.buffer(0)
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

    chile_wgs84 = build_chile_geometry(
        regions_geojson
    )

    chile_projected_full = transform(
        to_projected_transformer.transform,
        chile_wgs84,
    )

    if not chile_projected_full.is_valid:
        chile_projected_full = (
            chile_projected_full.buffer(0)
        )

    chile_projected = (
        build_quiz_land_mask(
            chile_projected_full
        )
    )

    seeds = load_candidate_seeds(
        seeds_geojson
    )

    seeds = filter_code_2_seeds(
        seeds
    )

    validate_retained_codes(
        seeds
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
        INTERMEDIATE_OUTPUT_PATH.stat().st_size
        / 1024
        / 1024
    )

    runtime_size_mb = (
        RUNTIME_OUTPUT_PATH.stat().st_size
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