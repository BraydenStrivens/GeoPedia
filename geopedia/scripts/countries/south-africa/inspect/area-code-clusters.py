"""
Inspect spatial clustering of South Africa OSM telephone area-code observations.

This diagnostic looks for geographically isolated phone-number observations
that may represent businesses or organizations using a landline number from a
different geographic area rather than evidence for the telephone area code at
the object's physical location.

Each telephone area code is analyzed independently. Observations are clustered
by geographic proximity, and every resulting cluster is summarized with:

- observation count
- percentage of observations for that code
- geographic bounds
- approximate cluster center
- distance to the largest cluster
- provinces
- municipalities

The script does not modify or filter any data. Its purpose is to determine
appropriate filtering rules before GeoPedia's South Africa area-code map is
regenerated.

Inputs:
    data/intermediate/countries/south-africa/osm/
    area-code-points.geojson

    data/intermediate/countries/south-africa/admin/
    wards.geojson

Run from the GeoPedia project root:
    python scripts/countries/south-africa/inspect/area-code-clusters.py

To save the full output:
    python scripts/countries/south-africa/inspect/area-code-clusters.py `
        > area-code-clusters-output.txt
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import Point, shape
from shapely.strtree import STRtree


POINTS_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "area-code-points.geojson"
)

WARDS_PATH = Path(
    "data/intermediate/countries/south-africa/admin/"
    "wards.geojson"
)


# Observations belonging to the same area code are considered connected when
# they are no more than this distance apart. Connected observations form a
# cluster transitively, so a geographic region can extend far beyond 50 km
# provided observations form a continuous chain.
CLUSTER_DISTANCE_KM = 50.0

EARTH_RADIUS_KM = 6371.0088


def load_feature_collection(
    path: Path,
    label: str,
) -> list[dict[str, Any]]:
    """Load and validate a GeoJSON FeatureCollection."""
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


def haversine_km(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    """Return great-circle distance between two coordinates in kilometers."""
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
        lon2_rad - lon1_rad
    )
    delta_lat = (
        lat2_rad - lat1_rad
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


def approximate_degree_radius(
    distance_km: float,
) -> float:
    """
    Convert kilometers to a conservative latitude/longitude search radius.

    This is used only to obtain STRtree candidates. Exact inclusion is checked
    afterward with Haversine distance.
    """
    return (
        distance_km / 90.0
    )


def join_points_to_wards(
    points: list[Point],
    ward_features: list[dict[str, Any]],
) -> list[dict[str, str | None]]:
    """
    Spatially join each telephone observation to its containing ward.

    Province and municipality names are retained only for diagnostics.
    """
    ward_geometries = [
        shape(
            feature["geometry"]
        )
        for feature in ward_features
    ]

    ward_tree = STRtree(
        ward_geometries
    )

    locations: list[
        dict[str, str | None]
    ] = []

    outside_count = 0

    for point in points:
        location: dict[
            str,
            str | None
        ] = {
            "province": None,
            "municipality": None,
        }

        candidates = ward_tree.query(
            point
        )

        for candidate in candidates:
            ward_index = int(
                candidate
            )

            if not ward_geometries[
                ward_index
            ].covers(
                point
            ):
                continue

            properties = ward_features[
                ward_index
            ].get(
                "properties",
                {},
            )

            location[
                "province"
            ] = properties.get(
                "province"
            )

            location[
                "municipality"
            ] = properties.get(
                "municipality"
            )

            break

        if (
            location["province"] is None
            and location["municipality"] is None
        ):
            outside_count += 1

        locations.append(
            location
        )

    print(
        f"Observations outside wards: {outside_count:,}"
    )

    return locations


def cluster_indices(
    indices: list[int],
    points: list[Point],
) -> list[list[int]]:
    """
    Cluster observations using distance-connected components.

    Two observations are directly connected when they are within
    CLUSTER_DISTANCE_KM. Connections are transitive.
    """
    if not indices:
        return []

    local_points = [
        points[index]
        for index in indices
    ]

    local_tree = STRtree(
        local_points
    )

    search_radius = (
        approximate_degree_radius(
            CLUSTER_DISTANCE_KM
        )
    )

    adjacency: list[
        set[int]
    ] = [
        set()
        for _ in local_points
    ]

    for local_index, point in enumerate(
        local_points
    ):
        envelope = point.buffer(
            search_radius
        ).envelope

        candidates = local_tree.query(
            envelope
        )

        for candidate in candidates:
            neighbor_local_index = int(
                candidate
            )

            if (
                neighbor_local_index
                <= local_index
            ):
                continue

            neighbor = local_points[
                neighbor_local_index
            ]

            distance = haversine_km(
                point.x,
                point.y,
                neighbor.x,
                neighbor.y,
            )

            if (
                distance
                > CLUSTER_DISTANCE_KM
            ):
                continue

            adjacency[
                local_index
            ].add(
                neighbor_local_index
            )

            adjacency[
                neighbor_local_index
            ].add(
                local_index
            )

    remaining = set(
        range(
            len(local_points)
        )
    )

    clusters: list[
        list[int]
    ] = []

    while remaining:
        start = remaining.pop()

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
            [
                indices[
                    local_index
                ]
                for local_index
                in component
            ]
        )

    clusters.sort(
        key=len,
        reverse=True,
    )

    return clusters


def cluster_center(
    cluster: list[int],
    points: list[Point],
) -> tuple[float, float]:
    """Return the mean coordinate of a cluster for diagnostics."""
    longitude = sum(
        points[index].x
        for index in cluster
    ) / len(cluster)

    latitude = sum(
        points[index].y
        for index in cluster
    ) / len(cluster)

    return (
        longitude,
        latitude,
    )


def minimum_cluster_distance(
    cluster_a: list[int],
    cluster_b: list[int],
    points: list[Point],
) -> float:
    """
    Return the minimum observation-to-observation distance between clusters.
    """
    minimum = math.inf

    for index_a in cluster_a:
        point_a = points[
            index_a
        ]

        for index_b in cluster_b:
            point_b = points[
                index_b
            ]

            distance = haversine_km(
                point_a.x,
                point_a.y,
                point_b.x,
                point_b.y,
            )

            if distance < minimum:
                minimum = distance

    return minimum


def format_counter(
    counter: Counter[str],
    limit: int,
) -> str:
    """Format the most common diagnostic location values."""
    if not counter:
        return "(none)"

    values = [
        f"{name}={count}"
        for name, count
        in counter.most_common(
            limit
        )
    ]

    if len(counter) > limit:
        values.append(
            f"+{len(counter) - limit} more"
        )

    return ", ".join(
        values
    )


def main() -> None:
    print("Loading area-code observations...")

    point_features = load_feature_collection(
        POINTS_PATH,
        "Area-code points",
    )

    points: list[Point] = []
    area_codes: list[str] = []

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

        geometry = shape(
            geometry_data
        )

        if geometry.geom_type != "Point":
            raise ValueError(
                "Area-code observation is not a Point."
            )

        points.append(
            geometry
        )

        area_codes.append(
            area_code
        )

    print(
        f"Loaded {len(points):,} observations."
    )

    print()
    print("Loading wards...")

    ward_features = load_feature_collection(
        WARDS_PATH,
        "Wards",
    )

    print(
        f"Loaded {len(ward_features):,} wards."
    )

    print()
    print("Joining observations to wards...")

    locations = join_points_to_wards(
        points,
        ward_features,
    )

    indices_by_code: defaultdict[
        str,
        list[int],
    ] = defaultdict(list)

    for index, area_code in enumerate(
        area_codes
    ):
        indices_by_code[
            area_code
        ].append(
            index
        )

    print()
    print("=" * 80)
    print(
        f"AREA-CODE CLUSTERS — "
        f"{CLUSTER_DISTANCE_KM:.0f} KM CONNECTION DISTANCE"
    )
    print("=" * 80)

    for area_code in sorted(
        indices_by_code
    ):
        indices = indices_by_code[
            area_code
        ]

        clusters = cluster_indices(
            indices,
            points,
        )

        total = len(
            indices
        )

        print()
        print("#" * 80)
        print(
            f"{area_code} — "
            f"{total:,} observations — "
            f"{len(clusters):,} clusters"
        )
        print("#" * 80)

        largest_cluster = (
            clusters[0]
        )

        for cluster_number, cluster in enumerate(
            clusters,
            start=1,
        ):
            percentage = (
                len(cluster)
                / total
                * 100
            )

            longitudes = [
                points[index].x
                for index in cluster
            ]

            latitudes = [
                points[index].y
                for index in cluster
            ]

            center_lon, center_lat = (
                cluster_center(
                    cluster,
                    points,
                )
            )

            provinces: Counter[str] = Counter()
            municipalities: Counter[str] = Counter()

            for index in cluster:
                province = locations[
                    index
                ][
                    "province"
                ]

                municipality = locations[
                    index
                ][
                    "municipality"
                ]

                if province:
                    provinces[
                        province
                    ] += 1

                if municipality:
                    municipalities[
                        municipality
                    ] += 1

            if cluster_number == 1:
                distance_text = "MAIN"
            else:
                distance = (
                    minimum_cluster_distance(
                        cluster,
                        largest_cluster,
                        points,
                    )
                )

                distance_text = (
                    f"{distance:.1f} km "
                    f"from main"
                )

            print()
            print(
                f"  Cluster {cluster_number}: "
                f"{len(cluster):,} observations "
                f"({percentage:.1f}%) — "
                f"{distance_text}"
            )

            print(
                "    Center: "
                f"{center_lat:.4f}, "
                f"{center_lon:.4f}"
            )

            print(
                "    Bounds: "
                f"{min(latitudes):.4f}, "
                f"{min(longitudes):.4f} "
                "to "
                f"{max(latitudes):.4f}, "
                f"{max(longitudes):.4f}"
            )

            print(
                "    Provinces: "
                + format_counter(
                    provinces,
                    5,
                )
            )

            print(
                "    Municipalities: "
                + format_counter(
                    municipalities,
                    8,
                )
            )


if __name__ == "__main__":
    main()