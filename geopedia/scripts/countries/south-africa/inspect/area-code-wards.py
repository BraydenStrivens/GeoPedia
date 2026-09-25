"""
Inspect how South Africa's OSM-derived telephone area-code observations
distribute across GeoPedia's ward geometries.

This script spatially joins extracted OSM telephone observations to wards and
reports how strongly each ward is associated with one or more geographic
telephone area codes.

It does not assign final area-code regions. Its purpose is to measure direct
OSM coverage, identify unobserved wards, identify mixed-code wards, and inspect
the special geographic relationship between Johannesburg's 010 and 011 codes.

Inputs:
    data/intermediate/countries/south-africa/osm/area-code-points.geojson
    public/data/countries/south-africa/geojson/wards.geojson

Run from the GeoPedia project root:
    python scripts/countries/south-africa/inspect/area-code-wards.py
"""

from __future__ import annotations

import json
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
    "public/data/countries/south-africa/geojson/wards.geojson"
)


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


def format_code_counts(
    counts: Counter[str],
) -> str:
    """
    Format area-code counts from most to least common.
    """
    ordered = sorted(
        counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    return ", ".join(
        f"{code}={count}"
        for code, count in ordered
    )


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

    point_features = load_feature_collection(
        AREA_CODE_POINTS_PATH,
        "Area-code points",
    )

    print(
        f"Loaded {len(point_features):,} observations."
    )

    # Each ward receives a counter such as:
    #
    #     {"012": 14}
    #
    # or, for a mixed ward:
    #
    #     {"010": 3, "011": 11}
    ward_code_counts: list[Counter[str]] = [
        Counter()
        for _ in ward_features
    ]

    outside_observations: list[
        dict[str, Any]
    ] = []

    print()
    print("Joining observations to wards...")

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

        point = shape(
            geometry_data
        )

        area_code = properties.get(
            "area_code"
        )

        if not isinstance(
            area_code,
            str,
        ):
            continue

        candidate_indices = ward_tree.query(
            point
        )

        matched_index: int | None = None

        for candidate_index in candidate_indices:
            index = int(candidate_index)

            if ward_geometries[index].covers(
                point
            ):
                matched_index = index
                break

        if matched_index is None:
            outside_observations.append(
                point_feature
            )
            continue

        ward_code_counts[
            matched_index
        ][area_code] += 1

    unobserved_indices: list[int] = []
    single_code_indices: list[int] = []
    mixed_code_indices: list[int] = []

    dominant_ward_counts: Counter[str] = Counter()

    for index, counts in enumerate(
        ward_code_counts
    ):
        if not counts:
            unobserved_indices.append(
                index
            )
            continue

        if len(counts) == 1:
            single_code_indices.append(
                index
            )
        else:
            mixed_code_indices.append(
                index
            )

        dominant_code = sorted(
            counts.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )[0][0]

        dominant_ward_counts[
            dominant_code
        ] += 1

    print()
    print("=" * 80)
    print("WARD COVERAGE")
    print("=" * 80)

    print(
        f"Total wards:                 "
        f"{len(ward_features):,}"
    )
    print(
        f"Single-code wards:           "
        f"{len(single_code_indices):,}"
    )
    print(
        f"Mixed-code wards:            "
        f"{len(mixed_code_indices):,}"
    )
    print(
        f"Wards with no observations:  "
        f"{len(unobserved_indices):,}"
    )
    print(
        f"Observations outside wards:  "
        f"{len(outside_observations):,}"
    )

    observed_wards = (
        len(single_code_indices)
        + len(mixed_code_indices)
    )

    coverage_percent = (
        observed_wards
        / len(ward_features)
        * 100
    )

    print(
        f"Direct ward coverage:        "
        f"{coverage_percent:.1f}%"
    )

    print()
    print("=" * 80)
    print("DOMINANT WARD COUNTS BY AREA CODE")
    print("=" * 80)

    all_codes = sorted(
        {
            code
            for counts in ward_code_counts
            for code in counts
        }
    )

    for code in all_codes:
        observation_count = sum(
            counts[code]
            for counts in ward_code_counts
        )

        print(
            f"{code}: "
            f"{dominant_ward_counts[code]:>4,} wards, "
            f"{observation_count:>5,} observations"
        )

    print()
    print("=" * 80)
    print("MIXED-CODE WARDS")
    print("=" * 80)

    if not mixed_code_indices:
        print("None.")
    else:
        # Put the most strongly mixed wards first.
        mixed_code_indices.sort(
            key=lambda index: (
                -sum(
                    ward_code_counts[
                        index
                    ].values()
                ),
                ward_features[
                    index
                ]["properties"].get(
                    "ward_id",
                    "",
                ),
            )
        )

        for index in mixed_code_indices:
            properties = ward_features[
                index
            ]["properties"]

            counts = ward_code_counts[
                index
            ]

            print()
            print(
                f"{properties.get('ward', '(unknown ward)')}"
            )
            print(
                f"  ward_id: "
                f"{properties.get('ward_id', '')}"
            )
            print(
                f"  municipality: "
                f"{properties.get('municipality', '')}"
            )
            print(
                f"  district: "
                f"{properties.get('district', '')}"
            )
            print(
                f"  province: "
                f"{properties.get('province', '')}"
            )
            print(
                f"  observations: "
                f"{format_code_counts(counts)}"
            )

    print()
    print("=" * 80)
    print("010 / 011 INSPECTION")
    print("=" * 80)

    code_010_011_indices = [
        index
        for index, counts in enumerate(
            ward_code_counts
        )
        if "010" in counts
        or "011" in counts
    ]

    municipality_totals: dict[
        tuple[str, str],
        Counter[str],
    ] = defaultdict(
        Counter
    )

    for index in code_010_011_indices:
        properties = ward_features[
            index
        ]["properties"]

        municipality = properties.get(
            "municipality",
            "",
        )

        municipality_id = properties.get(
            "municipality_id",
            "",
        )

        key = (
            municipality_id,
            municipality,
        )

        counts = ward_code_counts[
            index
        ]

        municipality_totals[key][
            "010"
        ] += counts["010"]

        municipality_totals[key][
            "011"
        ] += counts["011"]

    municipality_rows = sorted(
        municipality_totals.items(),
        key=lambda item: (
            -sum(
                item[1].values()
            ),
            item[0][1],
        ),
    )

    print()
    print("Municipality totals:")

    for (
        municipality_id,
        municipality,
    ), counts in municipality_rows:
        print(
            f"  {municipality} "
            f"({municipality_id}): "
            f"010={counts['010']:,}, "
            f"011={counts['011']:,}"
        )

    print()
    print("Wards containing 010 or 011:")

    code_010_011_indices.sort(
        key=lambda index: (
            ward_features[
                index
            ]["properties"].get(
                "municipality",
                "",
            ),
            ward_features[
                index
            ]["properties"].get(
                "ward",
                "",
            ),
        )
    )

    for index in code_010_011_indices:
        properties = ward_features[
            index
        ]["properties"]

        counts = ward_code_counts[
            index
        ]

        print(
            f"  "
            f"{properties.get('ward', '')} | "
            f"{properties.get('municipality', '')} | "
            f"010={counts['010']} | "
            f"011={counts['011']}"
        )

    print()
    print("=" * 80)
    print("UNOBSERVED WARDS BY PROVINCE")
    print("=" * 80)

    unobserved_by_province: Counter[str] = (
        Counter()
    )

    unobserved_by_municipality: Counter[
        tuple[str, str]
    ] = Counter()

    for index in unobserved_indices:
        properties = ward_features[
            index
        ]["properties"]

        province = properties.get(
            "province",
            "(unknown)",
        )

        municipality = properties.get(
            "municipality",
            "(unknown)",
        )

        municipality_id = properties.get(
            "municipality_id",
            "",
        )

        unobserved_by_province[
            province
        ] += 1

        unobserved_by_municipality[
            (
                municipality_id,
                municipality,
            )
        ] += 1

    for province, count in sorted(
        unobserved_by_province.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):
        print(
            f"{province}: {count:,}"
        )

    print()
    print("=" * 80)
    print("MUNICIPALITIES WITH MOST UNOBSERVED WARDS")
    print("=" * 80)

    for (
        municipality_id,
        municipality,
    ), count in unobserved_by_municipality.most_common(
        30
    ):
        print(
            f"{municipality} "
            f"({municipality_id}): "
            f"{count:,}"
        )


if __name__ == "__main__":
    main()