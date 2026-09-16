"""
Inspect geographic clusters of retained Chile area-code 2 OSM observations.

The purpose is to distinguish the real Santiago-area cluster from
non-geographic/centralized code-2 phone observations elsewhere in Chile.

Only observations with seed_severity <= 1 are considered, matching the
current Voronoi seed selection.

This script DOES NOT modify any data.

Input
-----
data/intermediate/countries/chile/inspection/
    osm-phone-code-seed-inspection.geojson

Run with:

    python scripts/countries/chile/inspect/osm-phone-code-2-clusters.py
"""

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "chile"
    / "inspection"
    / "osm-phone-code-seed-inspection.geojson"
)


AREA_CODE = "2"

MAX_SEED_SEVERITY = 1

# We'll inspect several radii instead of guessing one DBSCAN distance.
#
# min_samples=3 prevents two isolated chain-store observations from
# automatically becoming their own meaningful cluster.
TEST_RADII_KM = [
    2.0,
    5.0,
    10.0,
    20.0,
    40.0,
]

MIN_SAMPLES = 3

EARTH_RADIUS_KM = 6371.0088


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


def load_code_2_points(
    geojson: dict,
) -> list[dict]:
    points = []

    for feature in geojson.get(
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

        if area_code != AREA_CODE:
            continue

        severity = int(
            properties.get(
                "seed_severity",
                0,
            )
        )

        if severity > MAX_SEED_SEVERITY:
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

        points.append(
            {
                "lon": float(
                    coordinates[0]
                ),
                "lat": float(
                    coordinates[1]
                ),
                "severity": severity,
                "phone": properties.get(
                    "phone"
                ),
                "normalized_phone": (
                    properties.get(
                        "normalized_phone"
                    )
                ),
                "name": properties.get(
                    "name"
                ),
                "city": properties.get(
                    "city"
                ),
            }
        )

    return points


def haversine_km(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
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

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return (
        EARTH_RADIUS_KM
        * c
    )


def cluster_points(
    points: list[dict],
    radius_km: float,
):
    # DBSCAN with metric="haversine" expects radians in:
    #
    #     latitude, longitude
    #
    # order.
    coordinates_radians = np.radians(
        np.array(
            [
                [
                    point["lat"],
                    point["lon"],
                ]
                for point in points
            ]
        )
    )

    epsilon = (
        radius_km
        / EARTH_RADIUS_KM
    )

    model = DBSCAN(
        eps=epsilon,
        min_samples=MIN_SAMPLES,
        metric="haversine",
        algorithm="ball_tree",
    )

    labels = model.fit_predict(
        coordinates_radians
    )

    return labels


def summarize_cluster(
    cluster_points_list: list[dict],
) -> dict:
    lons = [
        point["lon"]
        for point in cluster_points_list
    ]

    lats = [
        point["lat"]
        for point in cluster_points_list
    ]

    center_lon = (
        sum(lons)
        / len(lons)
    )

    center_lat = (
        sum(lats)
        / len(lats)
    )

    city_counts = Counter(
        point["city"]
        for point in cluster_points_list
        if point["city"]
    )

    name_counts = Counter(
        point["name"]
        for point in cluster_points_list
        if point["name"]
    )

    phone_counts = Counter(
        point["normalized_phone"]
        for point in cluster_points_list
        if point["normalized_phone"]
    )

    max_radius_km = 0.0

    for point in cluster_points_list:
        distance = haversine_km(
            center_lon,
            center_lat,
            point["lon"],
            point["lat"],
        )

        max_radius_km = max(
            max_radius_km,
            distance,
        )

    return {
        "count": len(
            cluster_points_list
        ),
        "center_lon": center_lon,
        "center_lat": center_lat,
        "min_lon": min(
            lons
        ),
        "max_lon": max(
            lons
        ),
        "min_lat": min(
            lats
        ),
        "max_lat": max(
            lats
        ),
        "max_radius_km": (
            max_radius_km
        ),
        "cities": city_counts,
        "names": name_counts,
        "phones": phone_counts,
    }


def print_common_values(
    title: str,
    counts: Counter,
    limit: int = 8,
) -> None:
    if not counts:
        return

    values = counts.most_common(
        limit
    )

    formatted = ", ".join(
        f"{value} ({count})"
        for value, count
        in values
    )

    print(
        f"    {title}: "
        f"{formatted}"
    )


def inspect_radius(
    points: list[dict],
    radius_km: float,
) -> None:
    labels = cluster_points(
        points,
        radius_km,
    )

    cluster_groups = {}

    noise_points = []

    for point, label in zip(
        points,
        labels,
    ):
        if label == -1:
            noise_points.append(
                point
            )

            continue

        cluster_groups.setdefault(
            int(label),
            [],
        ).append(
            point
        )

    cluster_summaries = []

    for (
        cluster_id,
        cluster_point_list,
    ) in cluster_groups.items():
        summary = summarize_cluster(
            cluster_point_list
        )

        summary[
            "cluster_id"
        ] = cluster_id

        cluster_summaries.append(
            summary
        )

    cluster_summaries.sort(
        key=lambda summary: (
            -summary["count"]
        )
    )

    print()
    print(
        f"DBSCAN RADIUS: "
        f"{radius_km:.0f} km"
    )
    print("=" * 70)

    print(
        f"Clusters: "
        f"{len(cluster_summaries)}"
    )

    print(
        f"Clustered points: "
        f"{len(points) - len(noise_points)}"
    )

    print(
        f"Noise points: "
        f"{len(noise_points)}"
    )

    print()

    # Printing the largest 20 is enough to expose whether Santiago is
    # overwhelmingly dominant and what the secondary clusters contain.
    for rank, summary in enumerate(
        cluster_summaries[:20],
        start=1,
    ):
        print(
            f"  #{rank} "
            f"cluster {summary['cluster_id']}"
        )

        print(
            f"    points: "
            f"{summary['count']}"
        )

        print(
            "    center: "
            f"({summary['center_lon']:.5f}, "
            f"{summary['center_lat']:.5f})"
        )

        print(
            "    bounds: "
            f"lon "
            f"{summary['min_lon']:.5f} "
            f"to "
            f"{summary['max_lon']:.5f}, "
            f"lat "
            f"{summary['min_lat']:.5f} "
            f"to "
            f"{summary['max_lat']:.5f}"
        )

        print(
            "    max distance from center: "
            f"{summary['max_radius_km']:.2f} km"
        )

        print_common_values(
            "cities",
            summary["cities"],
        )

        print_common_values(
            "names",
            summary["names"],
        )

        print_common_values(
            "phones",
            summary["phones"],
        )

        print()

    if noise_points:
        noise_city_counts = Counter(
            point["city"]
            for point in noise_points
            if point["city"]
        )

        noise_name_counts = Counter(
            point["name"]
            for point in noise_points
            if point["name"]
        )

        noise_phone_counts = Counter(
            point[
                "normalized_phone"
            ]
            for point in noise_points
            if point[
                "normalized_phone"
            ]
        )

        print(
            "  Noise summary"
        )

        print_common_values(
            "cities",
            noise_city_counts,
            12,
        )

        print_common_values(
            "names",
            noise_name_counts,
            12,
        )

        print_common_values(
            "phones",
            noise_phone_counts,
            12,
        )


def main() -> None:
    geojson = load_geojson(
        INPUT_PATH
    )

    points = load_code_2_points(
        geojson
    )

    print()
    print(
        "CHILE AREA CODE 2 CLUSTER INSPECTION"
    )
    print("=" * 70)

    print(
        f"Retained code-2 points: "
        f"{len(points)}"
    )

    severity_counts = Counter(
        point["severity"]
        for point in points
    )

    print(
        "Severity counts: "
        + ", ".join(
            f"{severity}={count}"
            for severity, count
            in sorted(
                severity_counts.items()
            )
        )
    )

    for radius_km in TEST_RADII_KM:
        inspect_radius(
            points,
            radius_km,
        )


if __name__ == "__main__":
    main()