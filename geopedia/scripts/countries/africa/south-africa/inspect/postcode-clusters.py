"""
Inspect spatial clustering of South African OSM postcode observations.

This diagnostic groups observations for each four-digit postcode into
connected geographic clusters. Two observations are directly connected when
they are within CLUSTER_DISTANCE_KM of one another, and connected components
form the final clusters.

The purpose is to identify geographically isolated postcode observations
before postcode evidence is assigned to municipal wards. Unlike the telephone
area-code pipeline, this script does not assume that every postcode should
have only one legitimate geographic cluster.

No data is modified by this script.

Input:

    data/intermediate/countries/south-africa/osm/
    postcode-points.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-africa/inspect/postcode-clusters.py
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


POSTCODES_INPUT = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points.geojson"
)

CLUSTER_DISTANCE_KM = 50.0

EARTH_RADIUS_KM = 6371.0088

TOP_FRAGMENTED_POSTCODES = 100
MAX_CLUSTERS_TO_PRINT = 10


def load_feature_collection(
    path: Path,
) -> list[dict[str, Any]]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} has no valid features array."
        )

    return features


def haversine_km(
    longitude_1: float,
    latitude_1: float,
    longitude_2: float,
    latitude_2: float,
) -> float:
    """Return great-circle distance between two coordinates in kilometers."""
    longitude_1_rad = math.radians(
        longitude_1
    )
    latitude_1_rad = math.radians(
        latitude_1
    )
    longitude_2_rad = math.radians(
        longitude_2
    )
    latitude_2_rad = math.radians(
        latitude_2
    )

    delta_longitude = (
        longitude_2_rad
        - longitude_1_rad
    )
    delta_latitude = (
        latitude_2_rad
        - latitude_1_rad
    )

    a = (
        math.sin(
            delta_latitude / 2.0
        )
        ** 2
        + math.cos(latitude_1_rad)
        * math.cos(latitude_2_rad)
        * math.sin(
            delta_longitude / 2.0
        )
        ** 2
    )

    return (
        2.0
        * EARTH_RADIUS_KM
        * math.asin(
            math.sqrt(a)
        )
    )


def build_clusters(
    points: list[
        tuple[float, float]
    ],
) -> list[list[int]]:
    """
    Build distance-connected components for one postcode.

    A lightweight geographic grid limits distance comparisons to observations
    in nearby cells instead of comparing every point with every other point.
    """
    if not points:
        return []

    cell_size_degrees = (
        CLUSTER_DISTANCE_KM
        / 111.0
    )

    grid: dict[
        tuple[int, int],
        list[int],
    ] = defaultdict(list)

    parent = list(
        range(len(points))
    )

    rank = [
        0
        for _ in points
    ]

    def find(
        index: int,
    ) -> int:
        while parent[index] != index:
            parent[index] = parent[
                parent[index]
            ]
            index = parent[index]

        return index

    def union(
        left: int,
        right: int,
    ) -> None:
        left_root = find(left)
        right_root = find(right)

        if left_root == right_root:
            return

        if (
            rank[left_root]
            < rank[right_root]
        ):
            left_root, right_root = (
                right_root,
                left_root,
            )

        parent[right_root] = left_root

        if (
            rank[left_root]
            == rank[right_root]
        ):
            rank[left_root] += 1

    for index, (
        longitude,
        latitude,
    ) in enumerate(points):
        cell_x = math.floor(
            longitude
            / cell_size_degrees
        )
        cell_y = math.floor(
            latitude
            / cell_size_degrees
        )

        # Longitude degrees become geographically smaller toward the poles.
        # Searching two cells in each direction provides enough margin for
        # South Africa at the configured 50 km clustering distance.
        for offset_x in range(
            -2,
            3,
        ):
            for offset_y in range(
                -2,
                3,
            ):
                nearby_indexes = grid.get(
                    (
                        cell_x + offset_x,
                        cell_y + offset_y,
                    ),
                    [],
                )

                for other_index in (
                    nearby_indexes
                ):
                    other_longitude, other_latitude = (
                        points[
                            other_index
                        ]
                    )

                    if (
                        haversine_km(
                            longitude,
                            latitude,
                            other_longitude,
                            other_latitude,
                        )
                        <= CLUSTER_DISTANCE_KM
                    ):
                        union(
                            index,
                            other_index,
                        )

        grid[
            (
                cell_x,
                cell_y,
            )
        ].append(index)

    components: dict[
        int,
        list[int],
    ] = defaultdict(list)

    for index in range(
        len(points)
    ):
        components[
            find(index)
        ].append(index)

    clusters = list(
        components.values()
    )

    clusters.sort(
        key=len,
        reverse=True,
    )

    return clusters


def cluster_center(
    cluster: list[int],
    points: list[
        tuple[float, float]
    ],
) -> tuple[float, float]:
    """Return the mean coordinate of a cluster for diagnostics."""
    longitude = sum(
        points[index][0]
        for index in cluster
    ) / len(cluster)

    latitude = sum(
        points[index][1]
        for index in cluster
    ) / len(cluster)

    return (
        longitude,
        latitude,
    )


def distance_between_clusters(
    first_cluster: list[int],
    second_cluster: list[int],
    points: list[
        tuple[float, float]
    ],
) -> float:
    """
    Return the minimum observation-to-observation distance between clusters.

    This is more useful than centroid distance when deciding whether a small
    cluster is genuinely isolated from the main postcode geography.
    """
    minimum_distance = math.inf

    for first_index in first_cluster:
        first_longitude, first_latitude = (
            points[first_index]
        )

        for second_index in second_cluster:
            (
                second_longitude,
                second_latitude,
            ) = points[
                second_index
            ]

            distance = haversine_km(
                first_longitude,
                first_latitude,
                second_longitude,
                second_latitude,
            )

            minimum_distance = min(
                minimum_distance,
                distance,
            )

    return minimum_distance


def percentage(
    numerator: int,
    denominator: int,
) -> float:
    """Return a percentage while safely handling zero."""
    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100.0
    )


def main() -> None:
    """Inspect spatial clustering for every four-digit postcode."""
    print(
        "Loading postcode observations..."
    )

    features = load_feature_collection(
        POSTCODES_INPUT
    )

    observations_by_postcode: dict[
        str,
        list[
            tuple[float, float]
        ],
    ] = defaultdict(list)

    for feature in features:
        geometry = feature.get(
            "geometry"
        )

        properties = feature.get(
            "properties",
            {},
        )

        if (
            not isinstance(
                geometry,
                dict,
            )
            or geometry.get("type")
            != "Point"
        ):
            continue

        coordinates = geometry.get(
            "coordinates"
        )

        postcode = properties.get(
            "postcode"
        )

        if (
            not isinstance(
                coordinates,
                list,
            )
            or len(coordinates) < 2
            or not isinstance(
                postcode,
                str,
            )
        ):
            continue

        observations_by_postcode[
            postcode
        ].append(
            (
                float(coordinates[0]),
                float(coordinates[1]),
            )
        )

    print(
        f"Observations:      {len(features):,}"
    )
    print(
        "Distinct postcodes: "
        f"{len(observations_by_postcode):,}"
    )
    print(
        "Cluster distance:  "
        f"{CLUSTER_DISTANCE_KM:.1f} km"
    )

    results: list[
        dict[str, Any]
    ] = []

    total_clusters = 0
    single_cluster_postcodes = 0
    multi_cluster_postcodes = 0

    main_cluster_observations = 0
    secondary_cluster_observations = 0

    singleton_secondary_observations = 0

    print()
    print(
        "Building postcode clusters..."
    )

    for postcode in sorted(
        observations_by_postcode
    ):
        points = (
            observations_by_postcode[
                postcode
            ]
        )

        clusters = build_clusters(
            points
        )

        total = len(points)
        cluster_count = len(
            clusters
        )

        total_clusters += (
            cluster_count
        )

        if cluster_count == 1:
            single_cluster_postcodes += 1
        else:
            multi_cluster_postcodes += 1

        main_size = len(
            clusters[0]
        )

        secondary_size = (
            total
            - main_size
        )

        main_cluster_observations += (
            main_size
        )

        secondary_cluster_observations += (
            secondary_size
        )

        singleton_secondary_observations += sum(
            1
            for cluster in clusters[1:]
            if len(cluster) == 1
        )

        results.append(
            {
                "postcode": postcode,
                "points": points,
                "clusters": clusters,
                "total": total,
                "cluster_count": cluster_count,
                "main_size": main_size,
                "main_share": (
                    main_size
                    / total
                ),
                "secondary_size": secondary_size,
            }
        )

    print()
    print("Summary")
    print("-------")
    print(
        f"Total clusters:             "
        f"{total_clusters:,}"
    )
    print(
        f"Single-cluster postcodes:   "
        f"{single_cluster_postcodes:,} "
        f"({percentage(single_cluster_postcodes, len(results)):.1f}%)"
    )
    print(
        f"Multi-cluster postcodes:    "
        f"{multi_cluster_postcodes:,} "
        f"({percentage(multi_cluster_postcodes, len(results)):.1f}%)"
    )
    print(
        f"Main-cluster observations:  "
        f"{main_cluster_observations:,} "
        f"({percentage(main_cluster_observations, len(features)):.1f}%)"
    )
    print(
        f"Secondary observations:     "
        f"{secondary_cluster_observations:,} "
        f"({percentage(secondary_cluster_observations, len(features)):.1f}%)"
    )
    print(
        "Singleton secondary points: "
        f"{singleton_secondary_observations:,}"
    )

    main_share_buckets = {
        "100%": 0,
        "90-99%": 0,
        "75-89%": 0,
        "50-74%": 0,
        "<50%": 0,
    }

    for result in results:
        share = result[
            "main_share"
        ]

        if share == 1.0:
            main_share_buckets[
                "100%"
            ] += 1
        elif share >= 0.90:
            main_share_buckets[
                "90-99%"
            ] += 1
        elif share >= 0.75:
            main_share_buckets[
                "75-89%"
            ] += 1
        elif share >= 0.50:
            main_share_buckets[
                "50-74%"
            ] += 1
        else:
            main_share_buckets[
                "<50%"
            ] += 1

    print()
    print("Main-cluster share")
    print("------------------")

    for bucket in (
        "100%",
        "90-99%",
        "75-89%",
        "50-74%",
        "<50%",
    ):
        count = main_share_buckets[
            bucket
        ]

        print(
            f"{bucket:>6}: "
            f"{count:>5,} "
            f"({percentage(count, len(results)):5.1f}%)"
        )

    fragmented = [
        result
        for result in results
        if result[
            "cluster_count"
        ] > 1
    ]

    # Prioritize postcodes with the largest number of observations outside
    # their main cluster. Main-cluster share breaks ties.
    fragmented.sort(
        key=lambda result: (
            -result[
                "secondary_size"
            ],
            result[
                "main_share"
            ],
            result[
                "postcode"
            ],
        )
    )
    
    secondary_cluster_sizes: Counter[int] = Counter()
    secondary_distance_buckets: Counter[str] = Counter()
    secondary_size_distance: Counter[
        tuple[str, str]
    ] = Counter()

    for result in results:
        clusters = result[
            "clusters"
        ]

        if len(clusters) <= 1:
            continue

        points = result[
            "points"
        ]

        main_cluster = clusters[
            0
        ]

        for cluster in clusters[1:]:
            cluster_size = len(
                cluster
            )

            distance = (
                distance_between_clusters(
                    main_cluster,
                    cluster,
                    points,
                )
            )

            secondary_cluster_sizes[
                cluster_size
            ] += 1

            if distance < 100:
                distance_bucket = "50-99 km"
            elif distance < 200:
                distance_bucket = "100-199 km"
            elif distance < 500:
                distance_bucket = "200-499 km"
            else:
                distance_bucket = "500+ km"

            if cluster_size == 1:
                size_bucket = "1 point"
            elif cluster_size == 2:
                size_bucket = "2 points"
            elif cluster_size == 3:
                size_bucket = "3 points"
            else:
                size_bucket = "4+ points"

            secondary_distance_buckets[
                distance_bucket
            ] += 1

            secondary_size_distance[
                (
                    size_bucket,
                    distance_bucket,
                )
            ] += 1

    print()
    print("Secondary cluster sizes")
    print("-----------------------")

    for cluster_size in sorted(
        secondary_cluster_sizes
    ):
        count = secondary_cluster_sizes[
            cluster_size
        ]

        print(
            f"{cluster_size:>3} observation(s): "
            f"{count:>4,} cluster(s)"
        )

    print()
    print("Secondary cluster distances")
    print("---------------------------")

    distance_bucket_order = (
        "50-99 km",
        "100-199 km",
        "200-499 km",
        "500+ km",
    )

    for bucket in distance_bucket_order:
        print(
            f"{bucket:>10}: "
            f"{secondary_distance_buckets[bucket]:>4,} "
            "cluster(s)"
        )

    print()
    print("Secondary cluster size × distance")
    print("---------------------------------")

    size_bucket_order = (
        "1 point",
        "2 points",
        "3 points",
        "4+ points",
    )

    header = (
        f"{'Size':<10}"
        f"{'50-99':>8}"
        f"{'100-199':>10}"
        f"{'200-499':>10}"
        f"{'500+':>8}"
    )

    print(header)

    for size_bucket in size_bucket_order:
        values = [
            secondary_size_distance[
                (
                    size_bucket,
                    distance_bucket,
                )
            ]
            for distance_bucket
            in distance_bucket_order
        ]

        print(
            f"{size_bucket:<10}"
            f"{values[0]:>8,}"
            f"{values[1]:>10,}"
            f"{values[2]:>10,}"
            f"{values[3]:>8,}"
        )

    print()
    print(
        "Most fragmented postcodes "
        f"(up to {TOP_FRAGMENTED_POSTCODES})"
    )
    print(
        "============================================"
    )

    for result in fragmented[
        :TOP_FRAGMENTED_POSTCODES
    ]:
        postcode = result[
            "postcode"
        ]

        points = result[
            "points"
        ]

        clusters = result[
            "clusters"
        ]

        total = result[
            "total"
        ]

        print()
        print(
            f"{postcode}: "
            f"{total:,} observations, "
            f"{len(clusters):,} clusters, "
            f"main={len(clusters[0]):,} "
            f"({percentage(len(clusters[0]), total):.1f}%)"
        )

        main_cluster = clusters[
            0
        ]

        for cluster_index, cluster in enumerate(
            clusters[
                :MAX_CLUSTERS_TO_PRINT
            ],
            start=1,
        ):
            center_longitude, center_latitude = (
                cluster_center(
                    cluster,
                    points,
                )
            )

            if cluster_index == 1:
                distance_text = (
                    "main"
                )
            else:
                distance = (
                    distance_between_clusters(
                        main_cluster,
                        cluster,
                        points,
                    )
                )

                distance_text = (
                    f"{distance:.1f} km "
                    "from main"
                )

            print(
                f"  cluster {cluster_index}: "
                f"{len(cluster):,} "
                f"({percentage(len(cluster), total):.1f}%), "
                f"center=({center_latitude:.4f}, "
                f"{center_longitude:.4f}), "
                f"{distance_text}"
            )

        if (
            len(clusters)
            > MAX_CLUSTERS_TO_PRINT
        ):
            print(
                "  ... "
                f"{len(clusters) - MAX_CLUSTERS_TO_PRINT:,} "
                "additional clusters"
            )

    print()
    print("Inspection complete.")


if __name__ == "__main__":
    main()