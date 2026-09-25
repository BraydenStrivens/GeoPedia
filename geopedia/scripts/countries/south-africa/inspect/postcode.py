"""
Inspect the geographic observation clusters for one South African postcode.

This diagnostic reads the raw OSM postcode observations and groups the
observations for a requested postcode into connected geographic clusters
using the same 50 km distance used by the postcode-cleaning pipeline.

For each cluster it reports:

- Observation count
- Latitude/longitude bounds
- Approximate cluster center
- Distance from the main cluster
- Every observation and its OSM source

The largest cluster is treated as the main cluster using the same principle
as the cleaning pipeline.

This script does not modify any data.

Run from the GeoPedia project root:

    python scripts/countries/south-africa/inspect/postcode.py 9999

Another postcode can be inspected by replacing 9999 with its four-digit code.
"""

from __future__ import annotations

import json
import math
import sys
from collections import deque
from pathlib import Path
from typing import Any


INPUT_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points.geojson"
)

CLUSTER_DISTANCE_KM = 50.0

EARTH_RADIUS_KM = 6371.0088


def haversine_km(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    """Return the great-circle distance between two coordinates."""
    lon1_rad = math.radians(
        lon1
    )
    lat1_rad = math.radians(
        lat1
    )
    lon2_rad = math.radians(
        lon2
    )
    lat2_rad = math.radians(
        lat2
    )

    delta_lon = (
        lon2_rad
        - lon1_rad
    )
    delta_lat = (
        lat2_rad
        - lat1_rad
    )

    a = (
        math.sin(
            delta_lat / 2
        )
        ** 2
        + math.cos(
            lat1_rad
        )
        * math.cos(
            lat2_rad
        )
        * math.sin(
            delta_lon / 2
        )
        ** 2
    )

    return (
        2
        * EARTH_RADIUS_KM
        * math.asin(
            math.sqrt(a)
        )
    )


def load_observations(
    postcode: str,
) -> list[dict[str, Any]]:
    """Load all raw observations for one postcode."""
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    observations: list[
        dict[str, Any]
    ] = []

    for feature in data[
        "features"
    ]:
        properties = feature.get(
            "properties",
            {},
        )

        if (
            properties.get(
                "postcode"
            )
            != postcode
        ):
            continue

        geometry = feature.get(
            "geometry",
            {},
        )

        if (
            geometry.get("type")
            != "Point"
        ):
            continue

        coordinates = geometry.get(
            "coordinates"
        )

        if (
            not isinstance(
                coordinates,
                list,
            )
            or len(coordinates)
            < 2
        ):
            continue

        observations.append(
            {
                "lon": float(
                    coordinates[0]
                ),
                "lat": float(
                    coordinates[1]
                ),
                "properties": properties,
            }
        )

    return observations


def build_clusters(
    observations: list[
        dict[str, Any]
    ],
) -> list[list[int]]:
    """
    Build connected components using the configured distance threshold.

    Two observations are connected when they are within 50 km. Connections
    are transitive, matching the connected-component interpretation used by
    the postcode-cleaning pipeline.
    """
    count = len(
        observations
    )

    adjacency: list[
        list[int]
    ] = [
        []
        for _ in range(
            count
        )
    ]

    for first_index in range(
        count
    ):
        first = observations[
            first_index
        ]

        for second_index in range(
            first_index + 1,
            count,
        ):
            second = observations[
                second_index
            ]

            distance = haversine_km(
                first["lon"],
                first["lat"],
                second["lon"],
                second["lat"],
            )

            if (
                distance
                <= CLUSTER_DISTANCE_KM
            ):
                adjacency[
                    first_index
                ].append(
                    second_index
                )

                adjacency[
                    second_index
                ].append(
                    first_index
                )

    visited: set[int] = set()
    clusters: list[
        list[int]
    ] = []

    for start_index in range(
        count
    ):
        if (
            start_index
            in visited
        ):
            continue

        queue = deque(
            [start_index]
        )

        visited.add(
            start_index
        )

        cluster: list[int] = []

        while queue:
            current = queue.popleft()

            cluster.append(
                current
            )

            for neighbor in adjacency[
                current
            ]:
                if (
                    neighbor
                    in visited
                ):
                    continue

                visited.add(
                    neighbor
                )

                queue.append(
                    neighbor
                )

        clusters.append(
            cluster
        )

    clusters.sort(
        key=len,
        reverse=True,
    )

    return clusters


def cluster_center(
    cluster: list[int],
    observations: list[
        dict[str, Any]
    ],
) -> tuple[float, float]:
    """Return the mean longitude and latitude of a cluster."""
    longitude = sum(
        observations[index]["lon"]
        for index in cluster
    ) / len(cluster)

    latitude = sum(
        observations[index]["lat"]
        for index in cluster
    ) / len(cluster)

    return (
        longitude,
        latitude,
    )


def distance_between_clusters(
    first_cluster: list[int],
    second_cluster: list[int],
    observations: list[
        dict[str, Any]
    ],
) -> float:
    """Return the minimum point-to-point distance between two clusters."""
    minimum = math.inf

    for first_index in first_cluster:
        first = observations[
            first_index
        ]

        for second_index in second_cluster:
            second = observations[
                second_index
            ]

            distance = haversine_km(
                first["lon"],
                first["lat"],
                second["lon"],
                second["lat"],
            )

            minimum = min(
                minimum,
                distance,
            )

    return minimum


def print_cluster(
    number: int,
    cluster: list[int],
    observations: list[
        dict[str, Any]
    ],
    main_cluster: list[int],
) -> None:
    """Print detailed information about one observation cluster."""
    longitudes = [
        observations[index]["lon"]
        for index in cluster
    ]

    latitudes = [
        observations[index]["lat"]
        for index in cluster
    ]

    center_lon, center_lat = (
        cluster_center(
            cluster,
            observations,
        )
    )

    is_main = (
        cluster is main_cluster
    )

    print()
    print(
        "-" * 72
    )

    if is_main:
        print(
            f"Cluster {number} "
            f"(MAIN)"
        )
    else:
        print(
            f"Cluster {number} "
            f"(SECONDARY)"
        )

    print(
        "-" * 72
    )

    print(
        f"Observations:       "
        f"{len(cluster):,}"
    )

    print(
        f"Center:             "
        f"({center_lat:.6f}, "
        f"{center_lon:.6f})"
    )

    print(
        f"Latitude range:     "
        f"{min(latitudes):.6f} "
        f"to "
        f"{max(latitudes):.6f}"
    )

    print(
        f"Longitude range:    "
        f"{min(longitudes):.6f} "
        f"to "
        f"{max(longitudes):.6f}"
    )

    if not is_main:
        distance = (
            distance_between_clusters(
                main_cluster,
                cluster,
                observations,
            )
        )

        print(
            f"Distance from main: "
            f"{distance:.1f} km"
        )

    print()
    print(
        "Observations"
    )
    print(
        "------------"
    )

    for index in cluster:
        observation = (
            observations[index]
        )

        properties = observation[
            "properties"
        ]

        osm_type = properties.get(
            "osm_type",
            "unknown",
        )

        osm_id = properties.get(
            "osm_id",
            "unknown",
        )

        source_tag = properties.get(
            "source_tag",
            "unknown",
        )

        print(
            f"({observation['lat']:.6f}, "
            f"{observation['lon']:.6f})  "
            f"{osm_type} {osm_id}  "
            f"source={source_tag}"
        )


def main() -> None:
    """Inspect clusters for the postcode supplied on the command line."""
    if len(
        sys.argv
    ) != 2:
        raise SystemExit(
            "Usage: python "
            "scripts/countries/south-africa/inspect/"
            "postcode.py <4-digit-postcode>"
        )

    postcode = sys.argv[
        1
    ].strip()

    if (
        len(postcode) != 4
        or not postcode.isdigit()
    ):
        raise SystemExit(
            "Postcode must contain exactly four digits."
        )

    print(
        f"Reading {INPUT_PATH}..."
    )

    observations = (
        load_observations(
            postcode
        )
    )

    if not observations:
        raise SystemExit(
            f"No observations found for postcode {postcode}."
        )

    clusters = build_clusters(
        observations
    )

    main_cluster = clusters[
        0
    ]

    print()
    print(
        f"Postcode:           {postcode}"
    )
    print(
        f"Observations:       {len(observations):,}"
    )
    print(
        f"Clusters:           {len(clusters):,}"
    )
    print(
        f"Cluster distance:   {CLUSTER_DISTANCE_KM:.1f} km"
    )
    print(
        f"Main cluster size:  {len(main_cluster):,}"
    )

    secondary_count = (
        len(clusters)
        - 1
    )

    print(
        f"Secondary clusters: {secondary_count:,}"
    )

    for number, cluster in enumerate(
        clusters,
        start=1,
    ):
        print_cluster(
            number,
            cluster,
            observations,
            main_cluster,
        )


if __name__ == "__main__":
    main()