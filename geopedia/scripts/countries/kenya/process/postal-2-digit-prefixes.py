"""
Generates Kenya's 2-digit postal-prefix GeoJSON from GeoPedia's processed
3-digit postal-prefix dataset.

The 3-digit postal regions form a clean hierarchy under ten 2-digit prefixes:
00, 10, 20, 30, 40, 50, 60, 70, 80, and 90. This processor derives each
2-digit prefix from the accepted 3-digit answers and dissolves all geometries
belonging to the same parent prefix.

Multi-answer 3-digit regions are handled naturally. For example, the shared
605/607 geometry belongs to prefix 60 and is included only once in that
2-digit region.

Input:
    public/data/countries/kenya/geojson/
        3-digit-postal-prefixes.geojson

Output:
    public/data/countries/kenya/geojson/
        2-digit-postal-prefixes.geojson

Run from the GeoPedia project root:
    python scripts/countries/kenya/process/postal-2-digit-prefixes.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "kenya"
    / "geojson"
    / "3-digit-postal-prefixes.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "kenya"
    / "geojson"
    / "2-digit-postal-prefixes.geojson"
)

EXPECTED_SOURCE_FEATURE_COUNT = 43

EXPECTED_POSTAL_PREFIXES = {
    "00",
    "10",
    "20",
    "30",
    "40",
    "50",
    "60",
    "70",
    "80",
    "90",
}


def get_two_digit_prefix(prefix: str) -> str:
    """
    Converts a GeoPedia 3-digit postal answer into its 2-digit parent prefix.

    HelloQuiz represents Nairobi's broader postal region as "0", so it is
    normalized to "00". All other answers are expected to be three digits.
    """

    if prefix == "0":
        return "00"

    if len(prefix) != 3 or not prefix.isdigit():
        raise ValueError(
            f"Unexpected 3-digit postal prefix: {prefix!r}"
        )

    return prefix[:2]


def get_feature_two_digit_prefix(feature: dict) -> str:
    """
    Returns the single 2-digit parent prefix represented by a source feature.

    A source feature may accept multiple 3-digit answers, but all accepted
    answers must belong to the same 2-digit parent.
    """

    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError("Feature is missing a valid properties object.")

    prefixes = properties.get("postal_prefixes")

    if not isinstance(prefixes, list) or not prefixes:
        raise ValueError(
            "Feature is missing a non-empty postal_prefixes array."
        )

    two_digit_prefixes = {
        get_two_digit_prefix(prefix)
        for prefix in prefixes
    }

    if len(two_digit_prefixes) != 1:
        raise ValueError(
            "A 3-digit postal feature crosses multiple 2-digit prefixes: "
            f"{prefixes}"
        )

    return next(iter(two_digit_prefixes))


def main() -> None:
    """Builds and validates Kenya's 2-digit postal-prefix GeoJSON."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_PATH}"
        )

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        source = json.load(file)

    if source.get("type") != "FeatureCollection":
        raise ValueError(
            "Expected the source GeoJSON to be a FeatureCollection."
        )

    source_features = source.get("features")

    if not isinstance(source_features, list):
        raise ValueError(
            "Source GeoJSON is missing a valid features array."
        )

    if len(source_features) != EXPECTED_SOURCE_FEATURE_COUNT:
        raise ValueError(
            "Unexpected source feature count: "
            f"{len(source_features)} "
            f"(expected {EXPECTED_SOURCE_FEATURE_COUNT})."
        )

    geometries_by_prefix: dict[str, list] = defaultdict(list)

    for feature in source_features:
        two_digit_prefix = get_feature_two_digit_prefix(feature)

        geometry_data = feature.get("geometry")

        if not isinstance(geometry_data, dict):
            raise ValueError(
                f"Postal region {two_digit_prefix!r} contains a feature "
                "without valid geometry."
            )

        geometry = shape(geometry_data)

        if geometry.is_empty:
            raise ValueError(
                f"Postal region {two_digit_prefix!r} contains empty geometry."
            )

        if not geometry.is_valid:
            raise ValueError(
                f"Postal region {two_digit_prefix!r} contains invalid "
                "geometry."
            )

        geometries_by_prefix[two_digit_prefix].append(geometry)

    found_prefixes = set(geometries_by_prefix)

    if found_prefixes != EXPECTED_POSTAL_PREFIXES:
        missing = sorted(EXPECTED_POSTAL_PREFIXES - found_prefixes)
        unexpected = sorted(found_prefixes - EXPECTED_POSTAL_PREFIXES)

        raise ValueError(
            "Unexpected 2-digit postal-prefix set.\n"
            f"Missing: {missing}\n"
            f"Unexpected: {unexpected}"
        )

    output_features: list[dict] = []

    for postal_prefix in sorted(geometries_by_prefix):
        geometries = geometries_by_prefix[postal_prefix]

        dissolved_geometry = unary_union(geometries)

        if dissolved_geometry.is_empty:
            raise ValueError(
                f"Postal prefix {postal_prefix!r} produced empty geometry."
            )

        if not dissolved_geometry.is_valid:
            raise ValueError(
                f"Postal prefix {postal_prefix!r} produced invalid geometry."
            )

        if dissolved_geometry.geom_type not in {
            "Polygon",
            "MultiPolygon",
        }:
            raise ValueError(
                f"Postal prefix {postal_prefix!r} produced unexpected "
                f"geometry type {dissolved_geometry.geom_type!r}."
            )

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "postal_prefix": postal_prefix,
                },
                "geometry": mapping(dissolved_geometry),
            }
        )

    if len(output_features) != len(EXPECTED_POSTAL_PREFIXES):
        raise ValueError(
            "Unexpected output feature count: "
            f"{len(output_features)} "
            f"(expected {len(EXPECTED_POSTAL_PREFIXES)})."
        )

    output = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    input_size = INPUT_PATH.stat().st_size
    output_size = OUTPUT_PATH.stat().st_size

    print("Kenya 2-digit postal-prefix processing complete.")
    print()
    print(f"Source features:       {len(source_features)}")
    print(f"Output features:       {len(output_features)}")
    print(f"Quiz answers:          {len(output_features)}")
    print()
    print(
        "Prefixes:              "
        + ", ".join(
            feature["properties"]["postal_prefix"]
            for feature in output_features
        )
    )
    print()
    print(f"Input size:             {input_size / 1_000_000:.2f} MB")
    print(f"Output size:            {output_size / 1_000_000:.2f} MB")
    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()