"""
Generates TypeScript question arrays for Rwanda's administrative quizzes.

The canonical intermediate GeoJSON provides stable subdivision IDs, names,
and complete parent hierarchy information. Stable IDs are used as quiz
answers, while human-readable subdivision names are used as question displays.

Duplicate subdivision names are disambiguated with the minimum parent
hierarchy necessary to distinguish them.

The very large village question set is written to its own generated file so
that the standard administrative question data remains manageable.

Input:
    data/intermediate/countries/rwanda/admin/
        provinces.geojson
        districts.geojson
        sectors.geojson
        cells.geojson
        villages.geojson

Output:
    src/quiz/quizzes/countries/africa/rwanda/data/
        admin.ts
        villages.ts

Run from the GeoPedia project root:
    python scripts/countries/rwanda/generate/admin-quiz-data.py
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
    / "rwanda"
    / "admin"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "rwanda"
    / "data"
)

ADMIN_OUTPUT_PATH = OUTPUT_DIR / "admin.ts"
VILLAGES_OUTPUT_PATH = OUTPUT_DIR / "villages.ts"

EXPECTED_COUNTS = {
    "provinces": 5,
    "districts": 30,
    "sectors": 416,
    "cells": 2148,
    "villages": 14815,
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
    """Extracts the fields needed to generate one quiz question array."""

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
    Builds human-readable subdivision displays.

    Duplicate names progressively receive immediate-parent and higher-parent
    names until they are distinguished or the available hierarchy is
    exhausted. If multiple subdivisions still share the same display after
    using the full hierarchy, that duplicate display is retained because the
    stable subdivision ID remains the actual quiz and map identity.

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
            by_candidate: dict[
                str,
                list[dict[str, str]],
            ] = defaultdict(list)

            for record in unresolved:
                parents = [
                    record[property_name]
                    for property_name
                    in parent_properties[:parent_count]
                ]

                candidate = (
                    f"{name} ({', '.join(parents)})"
                )

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
            for record in unresolved:
                parents = [
                    record[property_name]
                    for property_name in parent_properties
                ]

                displays[record["id"]] = (
                    f"{name} ({', '.join(parents)})"
                    if parents
                    else name
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


def build_generated_file(
    description: str,
    regeneration_command: str,
    sections: list[str],
) -> str:
    """Builds a complete generated TypeScript question-data file."""

    return (
        "/**\n"
        f" * {description}\n"
        " *\n"
        " * Stable administrative IDs are used as quiz answers. Duplicate\n"
        " * subdivision names include parent names where useful for context;\n"
        " * duplicate displays may remain when the full hierarchy is identical.\n"
        " *\n"
        " * Do not edit this file manually.\n"
        " * Regenerate with:\n"
        f" *   {regeneration_command}\n"
        " */\n"
        "\n"
        'import type { FeatureQuizQuestion } from "@/types/quiz";\n'
        "\n"
        + "\n\n".join(sections)
        + "\n"
    )


def main() -> None:
    """Generates Rwanda's administrative quiz question arrays."""

    province_features = load_features(
        "provinces.geojson",
        EXPECTED_COUNTS["provinces"],
    )
    district_features = load_features(
        "districts.geojson",
        EXPECTED_COUNTS["districts"],
    )
    sector_features = load_features(
        "sectors.geojson",
        EXPECTED_COUNTS["sectors"],
    )
    cell_features = load_features(
        "cells.geojson",
        EXPECTED_COUNTS["cells"],
    )
    village_features = load_features(
        "villages.geojson",
        EXPECTED_COUNTS["villages"],
    )

    provinces = extract_records(
        province_features,
        "province_id",
        "province",
        [],
        "Provinces",
    )

    districts = extract_records(
        district_features,
        "district_id",
        "district",
        ["province"],
        "Districts",
    )

    sectors = extract_records(
        sector_features,
        "sector_id",
        "sector",
        [
            "district",
            "province",
        ],
        "Sectors",
    )

    cells = extract_records(
        cell_features,
        "cell_id",
        "cell",
        [
            "sector",
            "district",
            "province",
        ],
        "Cells",
    )

    villages = extract_records(
        village_features,
        "village_id",
        "village",
        [
            "cell",
            "sector",
            "district",
            "province",
        ],
        "Villages",
    )

    province_displays = build_displays(
        provinces,
        [],
    )
    district_displays = build_displays(
        districts,
        ["province"],
    )
    sector_displays = build_displays(
        sectors,
        [
            "district",
            "province",
        ],
    )
    cell_displays = build_displays(
        cells,
        [
            "sector",
            "district",
            "province",
        ],
    )
    village_displays = build_displays(
        villages,
        [
            "cell",
            "sector",
            "district",
            "province",
        ],
    )

    admin_sections = [
        build_question_array(
            "RWANDA_PROVINCES_QUIZ_QUESTIONS",
            provinces,
            province_displays,
        ),
        build_question_array(
            "RWANDA_DISTRICTS_QUIZ_QUESTIONS",
            districts,
            district_displays,
        ),
        build_question_array(
            "RWANDA_SECTORS_QUIZ_QUESTIONS",
            sectors,
            sector_displays,
        ),
        build_question_array(
            "RWANDA_CELLS_QUIZ_QUESTIONS",
            cells,
            cell_displays,
        ),
    ]

    village_sections = [
        build_question_array(
            "RWANDA_VILLAGES_QUIZ_QUESTIONS",
            villages,
            village_displays,
        ),
    ]

    command = (
        "python scripts/countries/rwanda/generate/"
        "admin-quiz-data.py"
    )

    admin_content = build_generated_file(
        "Generated question data for Rwanda's administrative quizzes.",
        command,
        admin_sections,
    )

    villages_content = build_generated_file(
        "Generated question data for Rwanda's village quiz.",
        command,
        village_sections,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ADMIN_OUTPUT_PATH.write_text(
        admin_content,
        encoding="utf-8",
    )

    VILLAGES_OUTPUT_PATH.write_text(
        villages_content,
        encoding="utf-8",
    )

    print("Rwanda administrative quiz data generated.")
    print()
    print(f"Provinces:  {len(provinces):>6,}")
    print(f"Districts:  {len(districts):>6,}")
    print(f"Sectors:    {len(sectors):>6,}")
    print(f"Cells:      {len(cells):>6,}")
    print(f"Villages:   {len(villages):>6,}")
    print()
    print(f"Admin output:    {ADMIN_OUTPUT_PATH}")
    print(f"Village output:  {VILLAGES_OUTPUT_PATH}")


if __name__ == "__main__":
    main()