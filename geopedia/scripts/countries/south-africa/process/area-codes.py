"""
Build South Africa telephone area-code geography from ward polygons and
OpenStreetMap landline telephone observations.

GeoPedia's South Africa area-code map is constructed by:

1. Grouping OSM geographic landline observations by their original area code.
2. Clustering each area's observations geographically and retaining only the
   largest 50 km-connected cluster as trusted geographic evidence.
3. Spatially joining those trusted observations to municipal wards.
4. Directly classifying wards with sufficiently strong phone evidence.
5. Iteratively classifying unresolved wards from adjacent classified wards.
6. Using nearby trusted OSM phone observations to resolve competing adjacent
   area codes and to provide geographic guidance in sparse areas.
7. Retaining assignment metadata so the inferred geography can be inspected
   before final area-code polygons are dissolved.

The main-cluster filter prevents isolated business, head-office, booking, or
other non-local telephone numbers from creating geographic area-code seeds far
from the code's primary region.

Clusters are calculated separately for each original area code before aliases
are applied. This means 010 and 011 establish their own trusted Johannesburg
observation clusters before 010 is normalized to 011 for geometry inference.

The classified ward GeoJSON is an intermediate debugging dataset. It preserves
the original ward geometry, trusted phone observations, final inferred area
code, grouping prefix, assignment method, and inference round.

010 is treated as an alternative Johannesburg code for geographic purposes.
Its trusted observations reinforce the 011 geographic region rather than
creating an independent ward-level polygon. The original 010 observations
remain identifiable in each ward's evidence.

Inputs:
    data/intermediate/countries/south-africa/osm/area-code-points.geojson
    data/intermediate/countries/south-africa/admin/wards.geojson

Output:
    data/intermediate/countries/south-africa/area-codes/
    classified-wards.geojson

Run from the GeoPedia project root:
    python scripts/countries/south-africa/process/area-codes.py
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import shape
from shapely.strtree import STRtree


AREA_CODE_POINTS_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "area-code-points.geojson"
)

WARDS_PATH = Path(
    "data/intermediate/countries/south-africa/admin/"
    "wards.geojson"
)

OUTPUT_PATH = Path(
    "data/intermediate/countries/south-africa/area-codes/"
    "classified-wards.geojson"
)


# Observations of the same original area code are connected when they are no
# more than this distance apart. Connected observations form clusters
# transitively. Only the largest cluster for each original area code is
# retained as trusted geographic evidence.
CLUSTER_DISTANCE_KM = 50.0

EARTH_RADIUS_KM = 6371.0088


# 010 is represented by the reference material as an alternative Johannesburg
# code. Its observations therefore support 011 geometry instead of competing
# for an independent ward-level region.
GEOMETRY_CODE_ALIASES = {
    "010": "011",
}


# Number of nearby trusted phone observations considered when adjacency
# presents more than one possible area code.
NEAREST_OBSERVATION_COUNT = 12


def load_feature_collection(
    path: Path,
    label: str,
) -> list[dict[str, Any]]:
    """
    Load and minimally validate a GeoJSON FeatureCollection.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{label} file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{label} must be a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{label} has no valid features array."
        )

    return features


def geometry_code(
    area_code: str,
) -> str:
    """
    Return the geographic region code used for geometry classification.
    """
    return GEOMETRY_CODE_ALIASES.get(
        area_code,
        area_code,
    )


def get_prefix_1(
    area_code: str,
) -> str:
    """
    Return the first meaningful digit after South Africa's trunk prefix 0.

    Examples:
        015 -> 1
        021 -> 2
        031 -> 3
        051 -> 5
    """
    if (
        len(area_code) != 3
        or not area_code.startswith("0")
        or not area_code.isdigit()
    ):
        raise ValueError(
            f"Unexpected area code: {area_code}"
        )

    return area_code[1]


def haversine_km(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    """
    Return great-circle distance between two WGS84 coordinates in kilometers.
    """
    lon1_rad = math.radians(lon1)
    lat1_rad = math.radians(lat1)
    lon2_rad = math.radians(lon2)
    lat2_rad = math.radians(lat2)

    delta_lon = lon2_rad - lon1_rad
    delta_lat = lat2_rad - lat1_rad

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_KM
        * math.asin(math.sqrt(a))
    )


def approximate_degree_radius(
    distance_km: float,
) -> float:
    """
    Return a conservative degree radius for STRtree candidate searches.

    Exact cluster membership is still determined with Haversine distance.
    """
    return distance_km / 90.0


def find_main_cluster(
    features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return the largest 50 km-connected component of one area's observations.

    Connections are transitive. A large geographic region may therefore span
    much more than 50 km as long as its observations form a continuous chain.
    """
    if not features:
        return []

    if len(features) == 1:
        return features.copy()

    geometries = [
        shape(feature["geometry"])
        for feature in features
    ]

    tree = STRtree(
        geometries
    )

    search_radius = approximate_degree_radius(
        CLUSTER_DISTANCE_KM
    )

    adjacency: list[set[int]] = [
        set()
        for _ in geometries
    ]

    for index, point in enumerate(
        geometries
    ):
        envelope = point.buffer(
            search_radius
        ).envelope

        candidates = tree.query(
            envelope
        )

        for candidate in candidates:
            neighbor_index = int(
                candidate
            )

            if neighbor_index <= index:
                continue

            neighbor = geometries[
                neighbor_index
            ]

            distance = haversine_km(
                point.x,
                point.y,
                neighbor.x,
                neighbor.y,
            )

            if distance > CLUSTER_DISTANCE_KM:
                continue

            adjacency[
                index
            ].add(
                neighbor_index
            )

            adjacency[
                neighbor_index
            ].add(
                index
            )

    remaining = set(
        range(len(features))
    )

    clusters: list[list[int]] = []

    while remaining:
        start = min(
            remaining
        )

        remaining.remove(
            start
        )

        component = [
            start
        ]

        stack = [
            start
        ]

        while stack:
            current = stack.pop()

            for neighbor in adjacency[
                current
            ]:
                if neighbor not in remaining:
                    continue

                remaining.remove(
                    neighbor
                )

                component.append(
                    neighbor
                )

                stack.append(
                    neighbor
                )

        clusters.append(
            component
        )

    # Size is the primary criterion. The minimum original feature index provides
    # deterministic behavior if two clusters happen to have identical sizes.
    clusters.sort(
        key=lambda cluster: (
            -len(cluster),
            min(cluster),
        )
    )

    return [
        features[index]
        for index in clusters[0]
    ]


def retain_main_area_code_clusters(
    point_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Retain only the largest spatial cluster for each original telephone code.

    Area codes are clustered before geographic aliases are applied. In
    particular, 010 and 011 are filtered independently before their trusted
    observations are combined as evidence for the 011 geographic region.
    """
    features_by_code: defaultdict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    ignored_features = 0

    for feature in point_features:
        geometry_data = feature.get(
            "geometry"
        )

        properties = feature.get(
            "properties",
            {},
        )

        area_code = properties.get(
            "area_code"
        )

        if (
            not geometry_data
            or not isinstance(
                area_code,
                str,
            )
        ):
            ignored_features += 1
            continue

        geometry = shape(
            geometry_data
        )

        if geometry.geom_type != "Point":
            raise ValueError(
                "Area-code observation is not a Point."
            )

        features_by_code[
            area_code
        ].append(
            feature
        )

    trusted_features: list[
        dict[str, Any]
    ] = []

    print()
    print("=" * 72)
    print("MAIN-CLUSTER OBSERVATION FILTER")
    print("=" * 72)
    print(
        f"Connection distance: "
        f"{CLUSTER_DISTANCE_KM:.0f} km"
    )

    print()
    print(
        f"{'Code':<6}"
        f"{'Raw':>8}"
        f"{'Kept':>8}"
        f"{'Removed':>10}"
        f"{'Kept %':>10}"
    )

    print("-" * 42)

    total_raw = 0
    total_kept = 0

    for area_code in sorted(
        features_by_code
    ):
        raw_features = features_by_code[
            area_code
        ]

        main_cluster = find_main_cluster(
            raw_features
        )

        raw_count = len(
            raw_features
        )

        kept_count = len(
            main_cluster
        )

        removed_count = (
            raw_count - kept_count
        )

        kept_percentage = (
            kept_count
            / raw_count
            * 100
        )

        total_raw += raw_count
        total_kept += kept_count

        trusted_features.extend(
            main_cluster
        )

        print(
            f"{area_code:<6}"
            f"{raw_count:>8,}"
            f"{kept_count:>8,}"
            f"{removed_count:>10,}"
            f"{kept_percentage:>9.1f}%"
        )

    print("-" * 42)

    print(
        f"{'TOTAL':<6}"
        f"{total_raw:>8,}"
        f"{total_kept:>8,}"
        f"{total_raw - total_kept:>10,}"
        f"{(total_kept / total_raw * 100):>9.1f}%"
    )

    if ignored_features:
        print()
        print(
            "Ignored malformed observations: "
            f"{ignored_features:,}"
        )

    print()
    print(
        "Trusted observations retained: "
        f"{len(trusted_features):,}"
    )

    return trusted_features


def classify_direct_evidence(
    counts: Counter[str],
) -> tuple[str | None, str | None]:
    """
    Classify a ward from trusted OSM phone observations when evidence is strong.

    010 observations are converted to 011 for geographic classification while
    remaining separate in the trusted observation metadata.

    Classification rules:

    - No observations:
      unresolved.

    - All geographic observations support one region:
      direct_unanimous.

    - At least three observations and the leading code has at least twice the
      runner-up count:
      direct_dominant.

    - At least five observations and the leader has at least 60 percent of all
      observations:
      direct_majority.

    Everything else remains unresolved for spatial inference.
    """
    if not counts:
        return None, None

    geographic_counts: Counter[str] = Counter()

    for area_code, count in counts.items():
        geographic_counts[
            geometry_code(area_code)
        ] += count

    ordered = sorted(
        geographic_counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    leading_code, leading_count = ordered[0]

    if len(ordered) == 1:
        return (
            leading_code,
            "direct_unanimous",
        )

    total = sum(
        geographic_counts.values()
    )

    runner_up_count = ordered[1][1]

    if (
        total >= 3
        and leading_count
        >= runner_up_count * 2
    ):
        return (
            leading_code,
            "direct_dominant",
        )

    if (
        total >= 5
        and leading_count / total >= 0.60
    ):
        return (
            leading_code,
            "direct_majority",
        )

    return None, "direct_ambiguous"


def build_adjacency(
    ward_geometries: list[Any],
    ward_tree: STRtree,
) -> list[set[int]]:
    """
    Build ward adjacency using shared polygon boundaries.

    Point-only corner contacts are ignored. Two wards are considered adjacent
    only when their boundaries share a line segment with positive length.
    """
    adjacency: list[set[int]] = [
        set()
        for _ in ward_geometries
    ]

    print()
    print("Building ward adjacency...")

    for index, geometry in enumerate(
        ward_geometries
    ):
        candidates = ward_tree.query(
            geometry
        )

        for candidate in candidates:
            neighbor_index = int(
                candidate
            )

            if neighbor_index <= index:
                continue

            neighbor_geometry = (
                ward_geometries[
                    neighbor_index
                ]
            )

            if not geometry.touches(
                neighbor_geometry
            ):
                continue

            shared_boundary = (
                geometry.boundary.intersection(
                    neighbor_geometry.boundary
                )
            )

            if shared_boundary.length <= 0:
                continue

            adjacency[
                index
            ].add(
                neighbor_index
            )

            adjacency[
                neighbor_index
            ].add(
                index
            )

    edge_count = (
        sum(
            len(neighbors)
            for neighbors in adjacency
        )
        // 2
    )

    print(
        f"Built {edge_count:,} ward adjacency edges."
    )

    return adjacency


def build_phone_point_index(
    point_features: list[dict[str, Any]],
) -> tuple[
    list[Any],
    list[str],
    STRtree,
]:
    """
    Build a spatial index of trusted geographic phone observations.

    Alternative codes are normalized to their geographic region code for
    inference.
    """
    point_geometries: list[Any] = []
    point_codes: list[str] = []

    for feature in point_features:
        geometry_data = feature.get(
            "geometry"
        )

        properties = feature.get(
            "properties",
            {},
        )

        area_code = properties.get(
            "area_code"
        )

        if (
            not geometry_data
            or not isinstance(
                area_code,
                str,
            )
        ):
            continue

        point_geometries.append(
            shape(
                geometry_data
            )
        )

        point_codes.append(
            geometry_code(
                area_code
            )
        )

    if not point_geometries:
        raise ValueError(
            "No trusted phone observations remain after cluster filtering."
        )

    return (
        point_geometries,
        point_codes,
        STRtree(
            point_geometries
        ),
    )


def nearest_phone_scores(
    ward_geometry: Any,
    candidate_codes: set[str],
    point_geometries: list[Any],
    point_codes: list[str],
    point_tree: STRtree,
) -> dict[str, float]:
    """
    Score candidate area codes from nearby trusted phone observations.

    The nearest observations belonging to candidate codes are found
    progressively. Each observation contributes inverse-distance evidence.

    Distance is measured in the source WGS84 coordinate system. This is used
    only as a local relative ranking signal, not as a physical distance
    measurement.
    """
    scores: defaultdict[str, float] = defaultdict(
        float
    )

    if not candidate_codes:
        return {}

    center = ward_geometry.representative_point()

    # STRtree.nearest gives the single nearest point. To collect several nearby
    # observations without constructing country-wide pairwise distances, expand
    # a search envelope until enough candidate observations are available.
    radius = 0.02

    candidate_indices: set[int] = set()

    while (
        len(candidate_indices)
        < NEAREST_OBSERVATION_COUNT
        and radius <= 8.0
    ):
        envelope = center.buffer(
            radius
        ).envelope

        queried = point_tree.query(
            envelope
        )

        for item in queried:
            point_index = int(
                item
            )

            if (
                point_codes[
                    point_index
                ]
                in candidate_codes
            ):
                candidate_indices.add(
                    point_index
                )

        radius *= 2

    if not candidate_indices:
        return {}

    ranked = sorted(
        candidate_indices,
        key=lambda point_index: (
            center.distance(
                point_geometries[
                    point_index
                ]
            ),
            point_index,
        ),
    )

    for point_index in ranked[
        :NEAREST_OBSERVATION_COUNT
    ]:
        code = point_codes[
            point_index
        ]

        distance = center.distance(
            point_geometries[
                point_index
            ]
        )

        # Prevent a point effectively coincident with the ward representative
        # point from producing an infinite score.
        distance = max(
            distance,
            0.0001,
        )

        scores[code] += (
            1.0 / distance
        )

    return dict(
        scores
    )


def choose_from_neighbors(
    ward_index: int,
    assignments: list[str | None],
    adjacency: list[set[int]],
    ward_geometries: list[Any],
    point_geometries: list[Any],
    point_codes: list[str],
    point_tree: STRtree,
) -> tuple[
    str | None,
    str | None,
    dict[str, int],
]:
    """
    Infer an unresolved ward from currently assigned adjacent wards.

    If all assigned neighbors agree, that code is used immediately.

    When neighboring codes disagree, shared-boundary support is the primary
    signal. Nearby trusted OSM phone observations are used as an independent
    tiebreaking signal.
    """
    neighbor_counts: Counter[str] = Counter()

    boundary_scores: defaultdict[
        str,
        float,
    ] = defaultdict(
        float
    )

    geometry = ward_geometries[
        ward_index
    ]

    for neighbor_index in adjacency[
        ward_index
    ]:
        code = assignments[
            neighbor_index
        ]

        if code is None:
            continue

        neighbor_counts[
            code
        ] += 1

        shared_boundary = (
            geometry.boundary.intersection(
                ward_geometries[
                    neighbor_index
                ].boundary
            )
        )

        boundary_scores[
            code
        ] += shared_boundary.length

    if not neighbor_counts:
        return (
            None,
            None,
            {},
        )

    candidate_codes = set(
        neighbor_counts
    )

    if len(candidate_codes) == 1:
        code = next(
            iter(
                candidate_codes
            )
        )

        return (
            code,
            "adjacency_unanimous",
            dict(
                neighbor_counts
            ),
        )

    max_boundary = max(
        boundary_scores.values()
    )

    if max_boundary > 0:
        normalized_boundary = {
            code: score / max_boundary
            for code, score
            in boundary_scores.items()
        }
    else:
        normalized_boundary = {
            code: 0.0
            for code in candidate_codes
        }

    max_neighbor_count = max(
        neighbor_counts.values()
    )

    normalized_neighbors = {
        code: (
            neighbor_counts[code]
            / max_neighbor_count
        )
        for code in candidate_codes
    }

    phone_scores = nearest_phone_scores(
        geometry,
        candidate_codes,
        point_geometries,
        point_codes,
        point_tree,
    )

    if phone_scores:
        max_phone_score = max(
            phone_scores.values()
        )

        normalized_phone = {
            code: (
                phone_scores.get(
                    code,
                    0.0,
                )
                / max_phone_score
            )
            for code in candidate_codes
        }
    else:
        normalized_phone = {
            code: 0.0
            for code in candidate_codes
        }

    # Boundary geometry is the strongest signal. Neighbor count provides
    # topological support, while trusted phone observations prevent inference
    # from becoming a purely self-propagating flood fill.
    combined_scores = {
        code: (
            normalized_boundary[
                code
            ]
            * 0.50
            + normalized_neighbors[
                code
            ]
            * 0.20
            + normalized_phone[
                code
            ]
            * 0.30
        )
        for code in candidate_codes
    }

    ordered = sorted(
        combined_scores.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    winning_code = ordered[0][0]

    return (
        winning_code,
        "adjacency_scored",
        dict(
            neighbor_counts
        ),
    )


def choose_from_nearest_phone(
    ward_geometry: Any,
    point_geometries: list[Any],
    point_codes: list[str],
    point_tree: STRtree,
) -> str:
    """
    Assign a ward with no classified neighbors from its nearest trusted
    geographic phone observation.

    This is a fallback intended only for wards that cannot be reached through
    the adjacency graph.
    """
    center = ward_geometry.representative_point()

    nearest_index = int(
        point_tree.nearest(
            center
        )
    )

    return point_codes[
        nearest_index
    ]


def main() -> None:
    print("Loading wards...")

    ward_features = load_feature_collection(
        WARDS_PATH,
        "Wards",
    )

    ward_geometries = [
        shape(feature["geometry"])
        for feature in ward_features
    ]

    ward_tree = STRtree(
        ward_geometries
    )

    print(
        f"Loaded {len(ward_features):,} wards."
    )

    print()
    print("Loading area-code observations...")

    raw_point_features = load_feature_collection(
        AREA_CODE_POINTS_PATH,
        "Area-code points",
    )

    print(
        f"Loaded {len(raw_point_features):,} raw observations."
    )

    point_features = retain_main_area_code_clusters(
        raw_point_features
    )

    (
        point_geometries,
        point_codes,
        point_tree,
    ) = build_phone_point_index(
        point_features
    )

    ward_raw_counts: list[
        Counter[str]
    ] = [
        Counter()
        for _ in ward_features
    ]

    outside_count = 0

    print()
    print("Joining trusted observations to wards...")

    for point_feature in point_features:
        geometry_data = point_feature.get(
            "geometry"
        )

        properties = point_feature.get(
            "properties",
            {},
        )

        if not geometry_data:
            continue

        area_code = properties.get(
            "area_code"
        )

        if not isinstance(
            area_code,
            str,
        ):
            continue

        point = shape(
            geometry_data
        )

        candidate_indices = ward_tree.query(
            point
        )

        matched_index: int | None = None

        for candidate_index in candidate_indices:
            index = int(
                candidate_index
            )

            if ward_geometries[index].covers(
                point
            ):
                matched_index = index
                break

        if matched_index is None:
            outside_count += 1
            continue

        ward_raw_counts[
            matched_index
        ][area_code] += 1

    print()
    print("Classifying direct evidence...")

    assignments: list[
        str | None
    ] = []

    assignment_methods: list[
        str | None
    ] = []

    assignment_rounds: list[
        int | None
    ] = []

    neighbor_evidence: list[
        dict[str, int] | None
    ] = []

    direct_assigned = 0
    ambiguous_count = 0
    unobserved_count = 0

    for raw_counts in ward_raw_counts:
        (
            area_code,
            method,
        ) = classify_direct_evidence(
            raw_counts
        )

        assignments.append(
            area_code
        )

        assignment_methods.append(
            method
        )

        if area_code is not None:
            assignment_rounds.append(
                0
            )

            direct_assigned += 1
        else:
            assignment_rounds.append(
                None
            )

        neighbor_evidence.append(
            None
        )

        if method == "direct_ambiguous":
            ambiguous_count += 1

        if not raw_counts:
            unobserved_count += 1

    print(
        f"Directly assigned {direct_assigned:,} wards."
    )

    adjacency = build_adjacency(
        ward_geometries,
        ward_tree,
    )

    print()
    print("=" * 72)
    print("ITERATIVE ADJACENCY INFERENCE")
    print("=" * 72)

    inference_round = 1

    while True:
        unresolved = [
            index
            for index, code in enumerate(
                assignments
            )
            if code is None
        ]

        if not unresolved:
            break

        proposed: dict[
            int,
            tuple[
                str,
                str,
                dict[str, int],
            ],
        ] = {}

        for index in unresolved:
            (
                code,
                method,
                evidence,
            ) = choose_from_neighbors(
                index,
                assignments,
                adjacency,
                ward_geometries,
                point_geometries,
                point_codes,
                point_tree,
            )

            if (
                code is not None
                and method is not None
            ):
                proposed[
                    index
                ] = (
                    code,
                    method,
                    evidence,
                )

        if not proposed:
            break

        # Apply an entire round simultaneously. Wards classified during this
        # round cannot influence another ward until the next round.
        for index, (
            code,
            method,
            evidence,
        ) in proposed.items():
            assignments[
                index
            ] = code

            assignment_methods[
                index
            ] = method

            assignment_rounds[
                index
            ] = inference_round

            neighbor_evidence[
                index
            ] = evidence

        remaining = (
            len(unresolved)
            - len(proposed)
        )

        print(
            f"Round {inference_round:>2}: "
            f"assigned {len(proposed):>4,}, "
            f"remaining {remaining:>4,}"
        )

        inference_round += 1

    unresolved_after_adjacency = [
        index
        for index, code in enumerate(
            assignments
        )
        if code is None
    ]

    print()
    print(
        "Unresolved after adjacency inference: "
        f"{len(unresolved_after_adjacency):,}"
    )

    if unresolved_after_adjacency:
        print()
        print(
            "Assigning remaining disconnected wards "
            "from nearest trusted phone observation..."
        )

        for index in (
            unresolved_after_adjacency
        ):
            code = choose_from_nearest_phone(
                ward_geometries[
                    index
                ],
                point_geometries,
                point_codes,
                point_tree,
            )

            assignments[
                index
            ] = code

            assignment_methods[
                index
            ] = "nearest_phone_fallback"

            assignment_rounds[
                index
            ] = inference_round

    if any(
        code is None
        for code in assignments
    ):
        raise ValueError(
            "Some wards remain unassigned."
        )

    print()
    print("Building classified ward output...")

    output_features: list[
        dict[str, Any]
    ] = []

    final_code_counts: Counter[str] = Counter()
    method_counts: Counter[str] = Counter()

    for index, ward_feature in enumerate(
        ward_features
    ):
        properties = dict(
            ward_feature.get(
                "properties",
                {},
            )
        )

        raw_counts = ward_raw_counts[
            index
        ]

        area_code = assignments[
            index
        ]

        if area_code is None:
            raise ValueError(
                f"Ward {index} has no area code."
            )

        method = assignment_methods[
            index
        ]

        properties[
            "area_code_observations"
        ] = {
            code: raw_counts[code]
            for code in sorted(
                raw_counts
            )
        }

        properties[
            "area_code_observation_count"
        ] = sum(
            raw_counts.values()
        )

        properties[
            "area_code"
        ] = area_code

        properties[
            "prefix_1"
        ] = get_prefix_1(
            area_code
        )

        properties[
            "area_code_assignment"
        ] = method

        properties[
            "area_code_assignment_round"
        ] = assignment_rounds[
            index
        ]

        if neighbor_evidence[
            index
        ] is not None:
            properties[
                "area_code_neighbor_evidence"
            ] = neighbor_evidence[
                index
            ]

        output_features.append(
            {
                "type": "Feature",
                "geometry": ward_feature[
                    "geometry"
                ],
                "properties": properties,
            }
        )

        final_code_counts[
            area_code
        ] += 1

        method_counts[
            str(method)
        ] += 1

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": output_features,
            },
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print()
    print("=" * 72)
    print("FINAL CLASSIFICATION SUMMARY")
    print("=" * 72)

    print(
        f"Total wards:                  "
        f"{len(ward_features):,}"
    )

    print(
        f"Trusted observations:         "
        f"{len(point_features):,}"
    )

    print(
        f"Directly assigned:            "
        f"{direct_assigned:,}"
    )

    print(
        f"Initially ambiguous:          "
        f"{ambiguous_count:,}"
    )

    print(
        f"Initially unobserved:         "
        f"{unobserved_count:,}"
    )

    print(
        f"Trusted obs. outside wards:   "
        f"{outside_count:,}"
    )

    print()
    print("Final assignment methods:")

    for method, count in sorted(
        method_counts.items()
    ):
        print(
            f"  {method:<24} "
            f"{count:>5,}"
        )

    print()
    print("Final wards by area code:")

    for area_code in sorted(
        final_code_counts
    ):
        print(
            f"  {area_code}: "
            f"{final_code_counts[area_code]:,}"
        )

    print()
    print("Final wards by 1-digit prefix:")

    prefix_counts: Counter[str] = Counter()

    for area_code, count in (
        final_code_counts.items()
    ):
        prefix_counts[
            get_prefix_1(
                area_code
            )
        ] += count

    for prefix in sorted(
        prefix_counts
    ):
        print(
            f"  {prefix}: "
            f"{prefix_counts[prefix]:,}"
        )

    print()
    print(
        "NOTE: Main clusters are selected separately "
        "for each original area code."
    )

    print(
        "NOTE: Trusted 010 observations reinforce "
        "the 011 geographic region."
    )

    size_mb = (
        OUTPUT_PATH.stat().st_size
        / (1024 * 1024)
    )

    print()
    print("Wrote:")
    print(f"  {OUTPUT_PATH}")
    print(f"  {size_mb:.2f} MB")


if __name__ == "__main__":
    main()