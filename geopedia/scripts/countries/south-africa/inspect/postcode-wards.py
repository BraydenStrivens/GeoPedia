"""
Inspect South African OSM postcode observations against municipal wards.

This diagnostic determines how well full four-digit postcodes and their
three-, two-, and one-digit prefixes can be represented using GeoPedia's
municipal ward geometry.

For each resolution, the script reports:

- observations falling inside wards
- observations outside all wards
- wards with no postcode observations
- wards containing one or multiple distinct values
- dominant-value strength within observed wards
- the distribution of distinct values per ward
- the most ambiguous wards

The unsimplified administrative ward dataset is intentionally used so the
results are not distorted by frontend geometry simplification.

Inputs:

    data/intermediate/countries/south-africa/admin/wards.geojson

    data/intermediate/countries/south-africa/osm/
    postcode-points.geojson

Run from the GeoPedia project root:

    python scripts/countries/south-africa/inspect/postcode-wards.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from shapely.geometry import Point, shape
from shapely.strtree import STRtree


WARDS_INPUT = Path(
    "data/intermediate/countries/south-africa/admin/"
    "wards.geojson"
)

POSTCODES_INPUT = Path(
    "data/intermediate/countries/south-africa/osm/"
    "postcode-points-cleaned.geojson"
)

RESOLUTIONS = (
    (
        "4-digit postcodes",
        "postcode",
    ),
    (
        "3-digit prefixes",
        "prefix_3",
    ),
    (
        "2-digit prefixes",
        "prefix_2",
    ),
    (
        "1-digit prefixes",
        "prefix_1",
    ),
)

AMBIGUOUS_LIMIT = 20


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


def ward_label(
    properties: dict[str, Any],
) -> str:
    """Create a useful diagnostic label for a ward."""
    ward = properties.get(
        "ward",
        properties.get(
            "ward_id",
            "Unknown ward",
        ),
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
    """Inspect postcode evidence at each geographic resolution."""
    print("Loading wards...")

    ward_features = load_feature_collection(
        WARDS_INPUT
    )

    print("Loading postcode observations...")

    postcode_features = load_feature_collection(
        POSTCODES_INPUT
    )

    print(
        f"Wards:                 "
        f"{len(ward_features):,}"
    )
    print(
        f"Postcode observations: "
        f"{len(postcode_features):,}"
    )

    print()
    print("Building ward spatial index...")

    ward_geometries = [
        shape(
            feature["geometry"]
        )
        for feature in ward_features
    ]

    tree = STRtree(
        ward_geometries
    )

    evidence: dict[
        str,
        dict[int, Counter[str]],
    ] = {
        property_name: defaultdict(
            Counter
        )
        for _, property_name
        in RESOLUTIONS
    }

    inside_observations = 0
    outside_observations = 0

    for observation in postcode_features:
        geometry = observation.get(
            "geometry"
        )

        properties = observation.get(
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

        if (
            not isinstance(
                coordinates,
                list,
            )
            or len(coordinates) < 2
        ):
            continue

        point = Point(
            coordinates[0],
            coordinates[1],
        )

        candidate_indexes = tree.query(
            point
        )

        matching_indexes = [
            int(index)
            for index in candidate_indexes
            if ward_geometries[
                int(index)
            ].covers(point)
        ]

        if not matching_indexes:
            outside_observations += 1
            continue

        # Administrative ward polygons should not overlap. If a point lies
        # exactly on a shared boundary, use the first matching ward so one
        # OSM observation is never counted twice.
        ward_index = matching_indexes[0]

        inside_observations += 1

        for _, property_name in RESOLUTIONS:
            value = properties.get(
                property_name
            )

            if not isinstance(
                value,
                str,
            ):
                raise ValueError(
                    "Postcode observation is missing "
                    f"{property_name}."
                )

            evidence[
                property_name
            ][
                ward_index
            ][
                value
            ] += 1

    print()
    print("Spatial matching")
    print("----------------")
    print(
        f"Inside wards:  "
        f"{inside_observations:,} "
        f"({percentage(inside_observations, len(postcode_features)):.1f}%)"
    )
    print(
        f"Outside wards: "
        f"{outside_observations:,} "
        f"({percentage(outside_observations, len(postcode_features)):.1f}%)"
    )

    for title, property_name in RESOLUTIONS:
        ward_evidence = evidence[
            property_name
        ]

        observed_wards = len(
            ward_evidence
        )

        no_data_wards = (
            len(ward_features)
            - observed_wards
        )

        single_value_wards = 0
        multi_value_wards = 0

        distinct_distribution: Counter[
            int
        ] = Counter()

        dominance_buckets = {
            "100%": 0,
            "90-99%": 0,
            "75-89%": 0,
            "50-74%": 0,
            "<50%": 0,
        }

        ambiguous: list[
            tuple[
                float,
                int,
                int,
                str,
                Counter[str],
            ]
        ] = []

        for ward_index, counts in (
            ward_evidence.items()
        ):
            distinct_count = len(
                counts
            )

            distinct_distribution[
                distinct_count
            ] += 1

            if distinct_count == 1:
                single_value_wards += 1
            else:
                multi_value_wards += 1

            total = sum(
                counts.values()
            )

            dominant_count = max(
                counts.values()
            )

            dominance = (
                dominant_count
                / total
            )

            if dominance == 1.0:
                dominance_buckets[
                    "100%"
                ] += 1
            elif dominance >= 0.90:
                dominance_buckets[
                    "90-99%"
                ] += 1
            elif dominance >= 0.75:
                dominance_buckets[
                    "75-89%"
                ] += 1
            elif dominance >= 0.50:
                dominance_buckets[
                    "50-74%"
                ] += 1
            else:
                dominance_buckets[
                    "<50%"
                ] += 1

            if distinct_count > 1:
                properties = (
                    ward_features[
                        ward_index
                    ].get(
                        "properties",
                        {},
                    )
                )

                ambiguous.append(
                    (
                        dominance,
                        -distinct_count,
                        -total,
                        ward_label(
                            properties
                        ),
                        counts,
                    )
                )

        ambiguous.sort()

        print()
        print("=" * 72)
        print(title.upper())
        print("=" * 72)

        print(
            f"Distinct values nationally: "
            f"{len(set(
                value
                for counts in ward_evidence.values()
                for value in counts
            )):,}"
        )

        print()
        print("Ward coverage")
        print("-------------")
        print(
            f"Observed wards:     "
            f"{observed_wards:,} "
            f"({percentage(observed_wards, len(ward_features)):.1f}%)"
        )
        print(
            f"No-data wards:      "
            f"{no_data_wards:,} "
            f"({percentage(no_data_wards, len(ward_features)):.1f}%)"
        )
        print(
            f"Single-value wards: "
            f"{single_value_wards:,} "
            f"({percentage(single_value_wards, observed_wards):.1f}% "
            "of observed)"
        )
        print(
            f"Multi-value wards:  "
            f"{multi_value_wards:,} "
            f"({percentage(multi_value_wards, observed_wards):.1f}% "
            "of observed)"
        )

        print()
        print("Distinct values per observed ward")
        print("---------------------------------")

        for distinct_count in sorted(
            distinct_distribution
        ):
            count = distinct_distribution[
                distinct_count
            ]

            print(
                f"{distinct_count:>3} value(s): "
                f"{count:>5,} "
                f"({percentage(count, observed_wards):5.1f}%)"
            )

        print()
        print("Dominant-value strength")
        print("-----------------------")

        for bucket in (
            "100%",
            "90-99%",
            "75-89%",
            "50-74%",
            "<50%",
        ):
            count = dominance_buckets[
                bucket
            ]

            print(
                f"{bucket:>6}: "
                f"{count:>5,} "
                f"({percentage(count, observed_wards):5.1f}%)"
            )

        if ambiguous:
            print()
            print(
                f"Most ambiguous wards "
                f"(up to {AMBIGUOUS_LIMIT})"
            )
            print(
                "--------------------------------"
            )

            for (
                dominance,
                negative_distinct,
                negative_total,
                label,
                counts,
            ) in ambiguous[
                :AMBIGUOUS_LIMIT
            ]:
                distinct_count = (
                    -negative_distinct
                )

                total = (
                    -negative_total
                )

                values = ", ".join(
                    f"{value}={count}"
                    for value, count
                    in counts.most_common()
                )

                print(
                    f"{label}"
                )
                print(
                    f"  observations={total:,}, "
                    f"values={distinct_count:,}, "
                    f"dominance={dominance * 100:.1f}%"
                )
                print(
                    f"  {values}"
                )

    print()
    print("Inspection complete.")


if __name__ == "__main__":
    main()