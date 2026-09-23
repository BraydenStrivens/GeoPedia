"""
Processes Kenya's HelloQuiz 3-digit postal-prefix GeoJSON for GeoPedia.

The HelloQuiz source contains purpose-built postal-region geometries under the
`AreaCode` property. Most features represent one 3-digit postal prefix, while
some represent multiple prefixes sharing the same geometry.

This processor:
- validates the expected HelloQuiz source structure
- splits space-separated multi-answer values into individual postal prefixes
- creates a stable scalar ID for each postal-region geometry
- derives the first digit for quiz grouping
- simplifies the source geometry for runtime use
- writes only the canonical properties required by GeoPedia

Input:
    data/raw/countries/kenya/postal/
        helloquiz_3_digit_postal_codes.geojson

Output:
    public/data/countries/kenya/geojson/
        3-digit-postal-prefixes.geojson

Run from the GeoPedia project root:
    python scripts/countries/kenya/process/postal-3-digit-prefixes.py
"""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import mapping, shape


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "countries"
    / "kenya"
    / "postal"
    / "helloquiz_3_digit_postal_codes.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "kenya"
    / "geojson"
    / "3-digit-postal-prefixes.geojson"
)

SIMPLIFY_TOLERANCE = 0.0005

EXPECTED_SOURCE_FEATURE_COUNT = 43
EXPECTED_OUTPUT_FEATURE_COUNT = 43
EXPECTED_ANSWER_COUNT = 45

EXPECTED_MULTI_ANSWER_REGIONS = {
    ("605", "607"),
    ("902", "904"),
}


def parse_postal_prefixes(value: object) -> list[str]:
    """
    Parses one HelloQuiz `AreaCode` value into its individual postal prefixes.

    A normal value such as "304" becomes ["304"], while a shared region such
    as "605 607" becomes ["605", "607"].
    """

    if not isinstance(value, str):
        raise ValueError(
            f"Expected AreaCode to be a string, got {type(value).__name__}."
        )

    prefixes = value.split()

    if not prefixes:
        raise ValueError("Encountered an empty AreaCode value.")

    for prefix in prefixes:
        if prefix == "0":
            continue

        if len(prefix) != 3 or not prefix.isdigit():
            raise ValueError(
                f"Unexpected 3-digit postal prefix: {prefix!r}"
            )

    if len(prefixes) != len(set(prefixes)):
        raise ValueError(
            f"AreaCode contains duplicate prefixes: {value!r}"
        )

    return prefixes


def get_first_digit(prefixes: list[str]) -> str:
    """
    Returns the common first digit shared by a postal region's prefixes.

    Multi-answer features are only valid when all accepted prefixes belong to
    the same first-digit grouping.
    """

    first_digits = {
        prefix[0]
        for prefix in prefixes
    }

    if len(first_digits) != 1:
        raise ValueError(
            "Postal prefixes sharing one geometry do not share a first digit: "
            f"{prefixes}"
        )

    return next(iter(first_digits))


def create_postal_region_id(prefixes: list[str]) -> str:
    """
    Creates a stable scalar identity for a postal-region geometry.

    Single-answer regions use their prefix directly. Multi-answer regions join
    their accepted prefixes with a hyphen.
    """

    return "-".join(prefixes)


def process_feature(feature: dict) -> tuple[dict, tuple[str, ...] | None]:
    """
    Converts one HelloQuiz feature into GeoPedia's canonical runtime format.

    Returns the processed feature and, when applicable, its multi-answer prefix
    tuple for dataset-level validation.
    """

    properties = feature.get("properties")

    if not isinstance(properties, dict):
        raise ValueError("Feature is missing a valid properties object.")

    if set(properties) != {"AreaCode"}:
        raise ValueError(
            "Unexpected source properties. "
            f"Expected only AreaCode, got: {sorted(properties)}"
        )

    prefixes = parse_postal_prefixes(properties["AreaCode"])
    first_digit = get_first_digit(prefixes)
    postal_region_id = create_postal_region_id(prefixes)

    geometry_data = feature.get("geometry")

    if not isinstance(geometry_data, dict):
        raise ValueError(
            f"Postal region {postal_region_id!r} is missing geometry."
        )

    if geometry_data.get("type") != "MultiPolygon":
        raise ValueError(
            f"Postal region {postal_region_id!r} has unexpected geometry "
            f"type {geometry_data.get('type')!r}; expected MultiPolygon."
        )

    geometry = shape(geometry_data)

    if geometry.is_empty:
        raise ValueError(
            f"Postal region {postal_region_id!r} has empty geometry."
        )

    if not geometry.is_valid:
        raise ValueError(
            f"Postal region {postal_region_id!r} has invalid source geometry."
        )

    simplified_geometry = geometry.simplify(
        SIMPLIFY_TOLERANCE,
        preserve_topology=True,
    )

    if simplified_geometry.is_empty:
        raise ValueError(
            f"Postal region {postal_region_id!r} became empty after "
            "simplification."
        )

    if not simplified_geometry.is_valid:
        raise ValueError(
            f"Postal region {postal_region_id!r} became invalid after "
            "simplification."
        )

    processed_feature = {
        "type": "Feature",
        "properties": {
            "postal_region_id": postal_region_id,
            "postal_prefixes": prefixes,
            "first_digit": first_digit,
        },
        "geometry": mapping(simplified_geometry),
    }

    multi_answer_region = (
        tuple(prefixes)
        if len(prefixes) > 1
        else None
    )

    return processed_feature, multi_answer_region


def main() -> None:
    """Processes and validates Kenya's 3-digit postal-prefix dataset."""

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

    processed_features: list[dict] = []
    seen_region_ids: set[str] = set()
    seen_prefixes: set[str] = set()
    multi_answer_regions: set[tuple[str, ...]] = set()

    for feature in source_features:
        processed_feature, multi_answer_region = process_feature(feature)

        properties = processed_feature["properties"]
        region_id = properties["postal_region_id"]
        prefixes = properties["postal_prefixes"]

        if region_id in seen_region_ids:
            raise ValueError(
                f"Duplicate postal_region_id: {region_id!r}"
            )

        seen_region_ids.add(region_id)

        for prefix in prefixes:
            if prefix in seen_prefixes:
                raise ValueError(
                    f"Postal prefix appears in multiple features: {prefix!r}"
                )

            seen_prefixes.add(prefix)

        if multi_answer_region is not None:
            multi_answer_regions.add(multi_answer_region)

        processed_features.append(processed_feature)

    if len(processed_features) != EXPECTED_OUTPUT_FEATURE_COUNT:
        raise ValueError(
            "Unexpected output feature count: "
            f"{len(processed_features)} "
            f"(expected {EXPECTED_OUTPUT_FEATURE_COUNT})."
        )

    if len(seen_prefixes) != EXPECTED_ANSWER_COUNT:
        raise ValueError(
            "Unexpected individual postal-prefix count: "
            f"{len(seen_prefixes)} "
            f"(expected {EXPECTED_ANSWER_COUNT})."
        )

    if multi_answer_regions != EXPECTED_MULTI_ANSWER_REGIONS:
        raise ValueError(
            "Unexpected multi-answer postal regions.\n"
            f"Found: {sorted(multi_answer_regions)}\n"
            f"Expected: {sorted(EXPECTED_MULTI_ANSWER_REGIONS)}"
        )

    processed_features.sort(
        key=lambda feature: feature["properties"]["postal_region_id"]
    )

    output = {
        "type": "FeatureCollection",
        "features": processed_features,
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

    reduction = (
        (1 - output_size / input_size) * 100
        if input_size
        else 0
    )

    print("Kenya 3-digit postal-prefix processing complete.")
    print()
    print(f"Source features:       {len(source_features)}")
    print(f"Output features:       {len(processed_features)}")
    print(f"Quiz answers:          {len(seen_prefixes)}")
    print(f"Multi-answer regions:  {len(multi_answer_regions)}")
    print(f"Simplify tolerance:    {SIMPLIFY_TOLERANCE}")
    print()
    print(f"Input size:             {input_size / 1_000_000:.2f} MB")
    print(f"Output size:            {output_size / 1_000_000:.2f} MB")
    print(f"Size reduction:         {reduction:.1f}%")
    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()