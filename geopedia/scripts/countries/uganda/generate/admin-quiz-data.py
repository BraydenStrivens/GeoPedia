"""
Generates TypeScript question arrays for Uganda's administrative quizzes.

The canonical intermediate GeoJSON provides stable administrative pcodes,
names, and parent hierarchy information. Stable IDs are used as quiz answers,
while human-readable subdivision names are used as question displays.

Each generated export is a complete FeatureQuizQuestion[] rather than an
ID-keyed lookup object. Duplicate subdivision names are disambiguated with the
minimum parent hierarchy necessary to distinguish them.

Input:
    data/intermediate/countries/uganda/admin/
        regions.geojson
        districts.geojson
        counties.geojson
        sub-counties.geojson

Output:
    src/quiz/quizzes/countries/africa/uganda/data/admin.ts

Run from the GeoPedia project root:
    python scripts/countries/uganda/generate/admin-quiz-data.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "uganda"
    / "admin"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "uganda"
    / "data"
    / "admin.ts"
)

EXPECTED_COUNTS = {
    "regions": 4,
    "districts": 135,
    "counties": 203,
    "sub-counties": 1520,
}


def load_features(
    filename: str,
    expected_count: int,
) -> list[dict[str, Any]]:
    """Loads and validates one canonical administrative dataset."""

    path = INPUT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{filename} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{filename} is missing a valid features array."
        )

    if len(features) != expected_count:
        raise ValueError(
            f"Unexpected feature count in {filename}: "
            f"{len(features)} (expected {expected_count})."
        )

    return features


def require_string(
    properties: dict[str, Any],
    key: str,
    *,
    feature_description: str,
) -> str:
    """Returns a required non-empty canonical string property."""

    value = properties.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{feature_description} has invalid {key}: {value!r}"
        )

    return value.strip()


def extract_records(
    features: list[dict[str, Any]],
    id_property: str,
    name_property: str,
    parent_properties: list[str],
    dataset_name: str,
) -> list[dict[str, str]]:
    """Extracts the fields needed to generate one quiz question dataset."""

    records: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for feature in features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"{dataset_name} contains a feature without valid properties."
            )

        subdivision_id = require_string(
            properties,
            id_property,
            feature_description=dataset_name,
        )

        if subdivision_id in seen_ids:
            raise ValueError(
                f"Duplicate {id_property} in {dataset_name}: "
                f"{subdivision_id!r}"
            )

        seen_ids.add(subdivision_id)

        record = {
            "id": subdivision_id,
            "name": require_string(
                properties,
                name_property,
                feature_description=f"{dataset_name} {subdivision_id}",
            ),
        }

        for parent_property in parent_properties:
            record[parent_property] = require_string(
                properties,
                parent_property,
                feature_description=f"{dataset_name} {subdivision_id}",
            )

        records.append(record)

    return records


def build_displays(
    records: list[dict[str, str]],
    parent_properties: list[str],
) -> dict[str, str]:
    """
    Builds human-readable displays, adding the minimum parent hierarchy needed
    to distinguish subdivisions that share the same name.

    Parent properties must be ordered from immediate parent outward.
    """

    by_name: dict[str, list[dict[str, str]]] = defaultdict(list)

    for record in records:
        by_name[record["name"]].append(record)

    displays: dict[str, str] = {}

    for name, same_name_records in by_name.items():
        if len(same_name_records) == 1:
            record = same_name_records[0]
            displays[record["id"]] = name
            continue

        unresolved = list(same_name_records)

        for parent_count in range(1, len(parent_properties) + 1):
            by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)

            for record in unresolved:
                parents = [
                    record[property_name]
                    for property_name in parent_properties[:parent_count]
                ]

                candidate = f"{name} ({', '.join(parents)})"
                by_candidate[candidate].append(record)

            next_unresolved: list[dict[str, str]] = []

            for candidate, candidate_records in by_candidate.items():
                if len(candidate_records) == 1:
                    record = candidate_records[0]
                    displays[record["id"]] = candidate
                else:
                    next_unresolved.extend(candidate_records)

            unresolved = next_unresolved

            if not unresolved:
                break

        if unresolved:
            ids = ", ".join(
                record["id"]
                for record in unresolved
            )

            raise ValueError(
                f"Could not uniquely disambiguate {name!r}: {ids}"
            )

    return displays


def ts_string(value: str) -> str:
    """Serializes a string as a TypeScript-compatible JSON string."""

    return json.dumps(
        value,
        ensure_ascii=False,
    )


def build_question_array(
    constant_name: str,
    records: list[dict[str, str]],
    displays: dict[str, str],
) -> str:
    """Builds one exported FeatureQuizQuestion array."""

    sorted_records = sorted(
        records,
        key=lambda record: (
            record["name"].casefold(),
            displays[record["id"]].casefold(),
            record["id"],
        ),
    )

    lines = [
        (
            f"export const {constant_name}: "
            "FeatureQuizQuestion[] = ["
        )
    ]

    for record in sorted_records:
        answer = ts_string(record["id"])
        display = ts_string(displays[record["id"]])

        lines.append(
            f"  {{ answer: {answer}, display: {display} }},"
        )

    lines.append("];")

    return "\n".join(lines)


def main() -> None:
    """Generates all Uganda administrative quiz question arrays."""

    region_features = load_features(
        "regions.geojson",
        EXPECTED_COUNTS["regions"],
    )
    district_features = load_features(
        "districts.geojson",
        EXPECTED_COUNTS["districts"],
    )
    county_features = load_features(
        "counties.geojson",
        EXPECTED_COUNTS["counties"],
    )
    sub_county_features = load_features(
        "sub-counties.geojson",
        EXPECTED_COUNTS["sub-counties"],
    )

    regions = extract_records(
        region_features,
        "region_id",
        "region",
        [],
        "Regions",
    )

    districts = extract_records(
        district_features,
        "district_id",
        "district",
        ["region"],
        "Districts",
    )

    counties = extract_records(
        county_features,
        "county_id",
        "county",
        [
            "district",
            "region",
        ],
        "Counties",
    )

    sub_counties = extract_records(
        sub_county_features,
        "sub_county_id",
        "sub_county",
        [
            "county",
            "district",
            "region",
        ],
        "Sub-counties",
    )

    region_displays = build_displays(
        regions,
        [],
    )
    district_displays = build_displays(
        districts,
        ["region"],
    )
    county_displays = build_displays(
        counties,
        [
            "district",
            "region",
        ],
    )
    sub_county_displays = build_displays(
        sub_counties,
        [
            "county",
            "district",
            "region",
        ],
    )

    sections = [
        build_question_array(
            "UGANDA_REGIONS_QUIZ_QUESTIONS",
            regions,
            region_displays,
        ),
        build_question_array(
            "UGANDA_DISTRICTS_QUIZ_QUESTIONS",
            districts,
            district_displays,
        ),
        build_question_array(
            "UGANDA_COUNTIES_QUIZ_QUESTIONS",
            counties,
            county_displays,
        ),
        build_question_array(
            "UGANDA_SUB_COUNTIES_QUIZ_QUESTIONS",
            sub_counties,
            sub_county_displays,
        ),
    ]

    content = (
        "/**\n"
        " * Generated question data for Uganda's administrative quizzes.\n"
        " *\n"
        " * Stable administrative pcodes are used as quiz answers. Duplicate\n"
        " * subdivision names are disambiguated with parent subdivision names.\n"
        " *\n"
        " * Do not edit this file manually.\n"
        " * Regenerate with:\n"
        " *   python scripts/countries/uganda/generate/admin-quiz-data.py\n"
        " */\n"
        "\n"
        'import type { FeatureQuizQuestion } from "@/types/quiz";\n'
        "\n"
        + "\n\n".join(sections)
        + "\n"
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )

    print("Uganda administrative quiz data generated.")
    print()
    print(f"Regions:       {len(regions)}")
    print(f"Districts:     {len(districts)}")
    print(f"Counties:      {len(counties)}")
    print(f"Sub-counties:  {len(sub_counties)}")
    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()