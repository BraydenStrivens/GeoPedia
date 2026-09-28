"""
Inspect spatial coverage of cleaned South African postcode observations.

This diagnostic measures how well the cleaned OSM postcode observations cover
South Africa's ward geography before postcode polygons are reconstructed.

For every ward, it measures:

- whether the ward contains postcode observations;
- the number of observations inside the ward;
- the distance from the ward representative point to the nearest postcode
  observation;
- the distance from the ward representative point to the nearest observation
  inside the same ward, when one exists.

It also summarizes nearest-observation distances nationally and separately for
wards with and without their own postcode observations.

This helps determine whether point-derived postcode regions can be constructed
directly or whether large observation gaps require stronger geographic
constraints.

Inputs:

    data/intermediate/countries/south-africa/admin/wards.geojson

    data/intermediate/countries/south-africa/osm/
    postcode-points-cleaned.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-africa/inspect/postcode-coverage.py
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from shapely.geometry import Point, shape
from shapely.strtree import STRtree


WARDS_PATH = Path(
    "data/intermediate/countries/south-africa/admin/"
    "wards.geojson"
)

POSTCODES_PATH = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points-cleaned.geojson"
)

EARTH_RADIUS_KM = 6371.0088

DISTANCE_BUCKETS_KM = (
    1,
    2,
    5,
    10,
    20,
    50,
    100,
)


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
    """Return great-circle distance between coordinates in kilometers."""
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


def percentile(
    values: list[float],
    percentage: float,
) -> float:
    """Return a linearly interpolated percentile from sorted values."""
    if not values:
        return math.nan

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (
        len(ordered) - 1
    ) * percentage

    lower_index = math.floor(
        position
    )
    upper_index = math.ceil(
        position
    )

    if lower_index == upper_index:
        return ordered[
            lower_index
        ]

    fraction = (
        position
        - lower_index
    )

    return (
        ordered[lower_index]
        * (1.0 - fraction)
        + ordered[upper_index]
        * fraction
    )


def distance_bucket(
    distance: float,
) -> str:
    """Return the configured bucket for a distance in kilometers."""
    previous = 0

    for maximum in DISTANCE_BUCKETS_KM:
        if distance <= maximum:
            return (
                f"{previous}-{maximum} km"
            )

        previous = maximum

    return (
        f"{DISTANCE_BUCKETS_KM[-1]}+ km"
    )


def print_distance_summary(
    title: str,
    distances: list[float],
) -> None:
    """Print percentile and bucket summaries for nearest-point distances."""
    print()
    print(title)
    print("-" * len(title))

    if not distances:
        print("No distances.")
        return

    print(
        f"Count:   {len(distances):,}"
    )
    print(
        f"Mean:    "
        f"{sum(distances) / len(distances):.2f} km"
    )
    print(
        f"Median:  "
        f"{percentile(distances, 0.50):.2f} km"
    )
    print(
        f"P75:     "
        f"{percentile(distances, 0.75):.2f} km"
    )
    print(
        f"P90:     "
        f"{percentile(distances, 0.90):.2f} km"
    )
    print(
        f"P95:     "
        f"{percentile(distances, 0.95):.2f} km"
    )
    print(
        f"P99:     "
        f"{percentile(distances, 0.99):.2f} km"
    )
    print(
        f"Maximum: "
        f"{max(distances):.2f} km"
    )

    counts = Counter(
        distance_bucket(
            distance
        )
        for distance in distances
    )

    print()
    print("Distance buckets")

    previous = 0

    for maximum in DISTANCE_BUCKETS_KM:
        label = (
            f"{previous}-{maximum} km"
        )

        count = counts[
            label
        ]

        percentage = (
            count
            / len(distances)
            * 100.0
        )

        print(
            f"{label:>10}: "
            f"{count:>5,} "
            f"({percentage:5.1f}%)"
        )

        previous = maximum

    final_label = (
        f"{DISTANCE_BUCKETS_KM[-1]}+ km"
    )

    count = counts[
        final_label
    ]

    percentage = (
        count
        / len(distances)
        * 100.0
    )

    print(
        f"{final_label:>10}: "
        f"{count:>5,} "
        f"({percentage:5.1f}%)"
    )


def ward_label(
    properties: dict[str, Any],
) -> str:
    """Return a useful human-readable ward label."""
    ward = properties.get(
        "ward",
        "Unknown ward",
    )

    municipality = properties.get(
        "municipality"
    )

    if municipality:
        return (
            f"{ward} — {municipality}"
        )

    return str(ward)


def main() -> None:
    """Inspect cleaned postcode observation coverage across wards."""
    print("Loading wards...")

    wards_data = load_feature_collection(
        WARDS_PATH
    )

    print(
        "Loading cleaned postcode "
        "observations..."
    )

    postcode_data = (
        load_feature_collection(
            POSTCODES_PATH
        )
    )

    ward_features = wards_data[
        "features"
    ]

    postcode_features = postcode_data[
        "features"
    ]

    print(
        f"Wards:                 "
        f"{len(ward_features):,}"
    )
    print(
        f"Postcode observations: "
        f"{len(postcode_features):,}"
    )

    print()
    print(
        "Building postcode spatial index..."
    )

    postcode_points = [
        shape(
            feature[
                "geometry"
            ]
        )
        for feature
        in postcode_features
    ]

    postcode_tree = STRtree(
        postcode_points
    )

    print(
        "Building ward spatial index..."
    )

    ward_geometries = [
        shape(
            feature[
                "geometry"
            ]
        )
        for feature
        in ward_features
    ]

    ward_tree = STRtree(
        ward_geometries
    )

    observations_per_ward = [
        0
        for _ in ward_features
    ]

    print()
    print(
        "Matching observations to wards..."
    )

    unmatched_observations = 0

    for point in postcode_points:
        candidate_indexes = (
            ward_tree.query(
                point
            )
        )

        matched_index: int | None = None

        for candidate_index in (
            candidate_indexes
        ):
            ward_index = int(
                candidate_index
            )

            ward_geometry = (
                ward_geometries[
                    ward_index
                ]
            )

            if ward_geometry.covers(
                point
            ):
                matched_index = (
                    ward_index
                )
                break

        if matched_index is None:
            unmatched_observations += 1
        else:
            observations_per_ward[
                matched_index
            ] += 1

    wards_with_observations = sum(
        count > 0
        for count
        in observations_per_ward
    )

    wards_without_observations = (
        len(ward_features)
        - wards_with_observations
    )

    print()
    print("Ward observation coverage")
    print("-------------------------")
    print(
        f"With observations:    "
        f"{wards_with_observations:,} "
        f"({wards_with_observations / len(ward_features) * 100:.1f}%)"
    )
    print(
        f"Without observations: "
        f"{wards_without_observations:,} "
        f"({wards_without_observations / len(ward_features) * 100:.1f}%)"
    )
    print(
        f"Unmatched points:      "
        f"{unmatched_observations:,}"
    )

    print()
    print(
        "Measuring nearest postcode "
        "observation from each ward..."
    )

    all_distances: list[float] = []
    observed_ward_distances: list[
        float
    ] = []
    empty_ward_distances: list[
        float
    ] = []

    ward_results: list[
        tuple[
            float,
            int,
            str,
            int,
            float,
            float,
        ]
    ] = []

    for ward_index, (
        feature,
        geometry,
    ) in enumerate(
        zip(
            ward_features,
            ward_geometries,
        )
    ):
        representative_point = (
            geometry.representative_point()
        )

        nearest_index = int(
            postcode_tree.nearest(
                representative_point
            )
        )

        nearest_point = (
            postcode_points[
                nearest_index
            ]
        )

        distance = haversine_km(
            representative_point.x,
            representative_point.y,
            nearest_point.x,
            nearest_point.y,
        )

        all_distances.append(
            distance
        )

        observation_count = (
            observations_per_ward[
                ward_index
            ]
        )

        if observation_count > 0:
            observed_ward_distances.append(
                distance
            )
        else:
            empty_ward_distances.append(
                distance
            )

        properties = feature.get(
            "properties",
            {}
        )

        ward_results.append(
            (
                distance,
                observation_count,
                ward_label(
                    properties
                ),
                ward_index,
                representative_point.y,
                representative_point.x,
            )
        )

    print_distance_summary(
        "All wards: nearest observation",
        all_distances,
    )

    print_distance_summary(
        "Wards with observations",
        observed_ward_distances,
    )

    print_distance_summary(
        "Wards without observations",
        empty_ward_distances,
    )

    print()
    print(
        "Most distant ward representative "
        "points (top 50)"
    )
    print(
        "-----------------------------------------"
    )

    ward_results.sort(
        key=lambda result: result[0],
        reverse=True,
    )

    for (
        distance,
        observation_count,
        label,
        _,
        latitude,
        longitude,
    ) in ward_results[
        :50
    ]:
        status = (
            "observed"
            if observation_count > 0
            else "no data"
        )

        print(
            f"{label}"
        )
        print(
            f"  distance={distance:.2f} km, "
            f"observations={observation_count:,}, "
            f"status={status}, "
            f"center=({latitude:.5f}, "
            f"{longitude:.5f})"
        )

    print()
    print("Inspection complete.")


if __name__ == "__main__":
    main()