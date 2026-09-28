"""
Clean South Africa postcode observations before postcode-area reconstruction.

Observations for each postcode are divided into geographic connected
components using the configured cluster distance.

The largest connected component for each postcode is treated as its main
geographic cluster and is always preserved, regardless of its observation
count.

Disconnected secondary clusters require stronger evidence because even a
small erroneous cluster can create a large false territory during Voronoi
reconstruction. Secondary clusters containing at least five observations are
preserved. Secondary clusters containing fewer than five observations are
removed.

This preserves strongly supported disconnected postcode geography while
preventing isolated or weakly supported OSM observations from creating
disproportionately large postcode regions.

Input:

    data/intermediate/countries/south-africa/osm/
    postcode-points.geojson

Output:

    data/intermediate/countries/south-africa/osm/
    postcode-points-cleaned.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-africa/process/clean-postcode-observations.py
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


INPUT_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points.geojson"
)

OUTPUT_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points-cleaned.geojson"
)

CLUSTER_DISTANCE_KM = 50.0

MIN_SECONDARY_CLUSTER_SIZE = 5

EARTH_RADIUS_KM = 6371.0088


def load_feature_collection(
    path: Path,
) -> dict[str, Any]:
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

    return data


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

    Observations within CLUSTER_DISTANCE_KM are connected. Connected chains
    belong to the same final cluster.
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
                    (
                        other_longitude,
                        other_latitude,
                    ) = points[
                        other_index
                    ]

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


def distance_between_clusters(
    first_cluster: list[int],
    second_cluster: list[int],
    points: list[
        tuple[float, float]
    ],
) -> float:
    """Return minimum observation-to-observation distance between clusters."""
    minimum_distance = math.inf

    for first_index in first_cluster:
        (
            first_longitude,
            first_latitude,
        ) = points[
            first_index
        ]

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


def observation_coordinates(
    feature: dict[str, Any],
) -> tuple[float, float]:
    """Return longitude and latitude for a postcode observation."""
    geometry = feature.get(
        "geometry"
    )

    if (
        not isinstance(
            geometry,
            dict,
        )
        or geometry.get("type")
        != "Point"
    ):
        raise ValueError(
            "Postcode observation does not contain Point geometry."
        )

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
        raise ValueError(
            "Postcode observation has invalid coordinates."
        )

    return (
        float(coordinates[0]),
        float(coordinates[1]),
    )


def observation_postcode(
    feature: dict[str, Any],
) -> str:
    """Return and validate the observation's four-digit postcode."""
    properties = feature.get(
        "properties",
        {}
    )

    postcode = properties.get(
        "postcode"
    )

    if (
        not isinstance(
            postcode,
            str,
        )
        or len(postcode) != 4
        or not postcode.isdigit()
    ):
        raise ValueError(
            f"Invalid postcode observation: {postcode!r}"
        )

    return postcode


def format_removed_observation(
    feature: dict[str, Any],
    distance: float,
) -> str:
    """Create an audit-line description for a removed observation."""
    properties = feature.get(
        "properties",
        {}
    )

    longitude, latitude = (
        observation_coordinates(
            feature
        )
    )

    postcode = properties.get(
        "postcode",
        "?",
    )

    osm_type = properties.get(
        "osm_type",
        "?",
    )

    osm_id = properties.get(
        "osm_id",
        "?",
    )

    source_tag = properties.get(
        "source_tag",
        "?",
    )

    return (
        f"{postcode}: "
        f"({latitude:.6f}, {longitude:.6f}), "
        f"{distance:.1f} km from main, "
        f"{osm_type} {osm_id}, "
        f"source={source_tag}"
    )


def main() -> None:
    """Remove clearly isolated singleton postcode observations."""
    print(
        f"Reading {INPUT_PATH}..."
    )

    data = load_feature_collection(
        INPUT_PATH
    )

    features: list[
        dict[str, Any]
    ] = data[
        "features"
    ]

    feature_indexes_by_postcode: dict[
        str,
        list[int],
    ] = defaultdict(list)

    for feature_index, feature in enumerate(
        features
    ):
        postcode = observation_postcode(
            feature
        )

        feature_indexes_by_postcode[
            postcode
        ].append(
            feature_index
        )

    print(
        f"Input observations:  {len(features):,}"
    )
    print(
        "Distinct postcodes:  "
        f"{len(feature_indexes_by_postcode):,}"
    )
    print(
        "Cluster distance:    "
        f"{CLUSTER_DISTANCE_KM:.1f} km"
    )

    removed_indexes: set[int] = set()

    removed_records: list[
        tuple[
            str,
            float,
            dict[str, Any],
        ]
    ] = []

    postcode_count_with_removals = 0

    for postcode in sorted(
        feature_indexes_by_postcode
    ):
        global_indexes = (
            feature_indexes_by_postcode[
                postcode
            ]
        )

        points = [
            observation_coordinates(
                features[
                    feature_index
                ]
            )
            for feature_index
            in global_indexes
        ]

        clusters = build_clusters(
            points
        )

        if len(clusters) <= 1:
            continue

        main_cluster = clusters[
            0
        ]

        postcode_removed = False

        for secondary_cluster in clusters[
            1:
        ]:
            if (
                len(secondary_cluster)
                >= MIN_SECONDARY_CLUSTER_SIZE
            ):
                continue

            distance = (
                distance_between_clusters(
                    main_cluster,
                    secondary_cluster,
                    points,
                )
            )

            local_index = (
                secondary_cluster[
                    0
                ]
            )

            global_index = (
                global_indexes[
                    local_index
                ]
            )

            removed_indexes.add(
                global_index
            )

            removed_records.append(
                (
                    postcode,
                    distance,
                    features[
                        global_index
                    ],
                )
            )

            postcode_removed = True

        if postcode_removed:
            postcode_count_with_removals += 1

    cleaned_features = [
        feature
        for feature_index, feature
        in enumerate(features)
        if feature_index
        not in removed_indexes
    ]

    removed_records.sort(
        key=lambda record: (
            record[0],
            -record[1],
        )
    )

    print()
    print("Removed observations")
    print("--------------------")

    if not removed_records:
        print("None")
    else:
        for (
            _,
            distance,
            feature,
        ) in removed_records:
            print(
                format_removed_observation(
                    feature,
                    distance,
                )
            )

    print()
    print("Summary")
    print("-------")
    print(
        f"Input observations:        "
        f"{len(features):,}"
    )
    print(
        f"Removed observations:      "
        f"{len(removed_indexes):,}"
    )
    print(
        f"Remaining observations:    "
        f"{len(cleaned_features):,}"
    )
    print(
        f"Postcodes with removals:   "
        f"{postcode_count_with_removals:,}"
    )

    if features:
        removed_percentage = (
            len(removed_indexes)
            / len(features)
            * 100.0
        )
    else:
        removed_percentage = 0.0

    print(
        f"Removed percentage:        "
        f"{removed_percentage:.3f}%"
    )

    remaining_postcodes = {
        observation_postcode(
            feature
        )
        for feature
        in cleaned_features
    }

    print(
        f"Remaining postcodes:       "
        f"{len(remaining_postcodes):,}"
    )

    output_data = {
        "type": "FeatureCollection",
        "features": cleaned_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output_data,
            file,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    print()
    print(
        f"Wrote {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()