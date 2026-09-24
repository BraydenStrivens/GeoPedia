"""
Generates TypeScript question data for Namibia's administrative quizzes.

Questions use the canonical administrative pcodes as stable answers and the
human-readable subdivision names as display values. Namibia's region and
constituency names are unique in the canonical datasets, so no parent-name
disambiguation is required.

Input:
    data/intermediate/countries/namibia/admin/
        regions.geojson
        constituencies.geojson

Output:
    src/quiz/quizzes/countries/africa/namibia/data/admin.ts

Run from the GeoPedia project root:
    python scripts/countries/namibia/generate/admin-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "intermediate"
    / "countries"
    / "namibia"
    / "admin"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "africa"
    / "namibia"
    / "data"
    / "admin.ts"
)

DATASETS = [
    {
        "filename": "regions.geojson",
        "constant": "NAMIBIA_REGIONS_QUIZ_QUESTIONS",
        "id_property": "region_id",
        "name_property": "region",
        "expected_count": 14,
    },
    {
        "filename": "constituencies.geojson",
        "constant": "NAMIBIA_CONSTITUENCIES_QUIZ_QUESTIONS",
        "id_property": "constituency_id",
        "name_property": "constituency",
        "expected_count": 107,
    },
]


def load_geojson(path: Path) -> dict[str, Any]:
    """Loads and validates a canonical GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path.name} is missing a valid features array."
        )

    return data


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


def load_questions(
    config: dict[str, Any],
) -> list[tuple[str, str]]:
    """
    Loads one canonical dataset and returns stable ID/display-name pairs.
    """

    path = INPUT_DIR / config["filename"]
    data = load_geojson(path)
    features = data["features"]

    if len(features) != config["expected_count"]:
        raise ValueError(
            f"{config['filename']} contains {len(features)} features; "
            f"expected {config['expected_count']}."
        )

    questions: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for feature in features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"{config['filename']} contains a feature "
                "without valid properties."
            )

        answer = require_string(
            properties,
            config["id_property"],
            feature_description=config["filename"],
        )

        display = require_string(
            properties,
            config["name_property"],
            feature_description=f"{config['filename']} {answer}",
        )

        if answer in seen_ids:
            raise ValueError(
                f"{config['filename']} contains duplicate ID "
                f"{answer!r}."
            )

        if display in seen_names:
            raise ValueError(
                f"{config['filename']} contains duplicate display "
                f"name {display!r}."
            )

        seen_ids.add(answer)
        seen_names.add(display)

        questions.append((answer, display))

    questions.sort(
        key=lambda question: question[1].casefold()
    )

    return questions


def ts_string(value: str) -> str:
    """Returns a JSON-escaped string suitable for TypeScript output."""

    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_question_array(
    constant: str,
    questions: list[tuple[str, str]],
) -> str:
    """Renders one FeatureQuizQuestion TypeScript array."""

    lines = [
        (
            f"export const {constant}: "
            "FeatureQuizQuestion[] = ["
        )
    ]

    for answer, display in questions:
        lines.append(
            "  { "
            f"answer: {ts_string(answer)}, "
            f"display: {ts_string(display)} "
            "},"
        )

    lines.append("];")

    return "\n".join(lines)


def build_output(
    generated_datasets: list[
        tuple[dict[str, Any], list[tuple[str, str]]]
    ],
) -> str:
    """Builds the complete generated TypeScript module."""

    sections = [
        """/**
 * Generated question data for Namibia's administrative quizzes.
 *
 * DO NOT EDIT MANUALLY.
 *
 * Generated from the canonical intermediate administrative GeoJSON.
 *
 * Regenerate with:
 * python scripts/countries/namibia/generate/admin-quiz-data.py
 */

import type { FeatureQuizQuestion } from "@/quiz/types";
"""
    ]

    for config, questions in generated_datasets:
        sections.append(
            render_question_array(
                config["constant"],
                questions,
            )
        )

    return "\n\n".join(sections) + "\n"


def main() -> None:
    """Generates Namibia's administrative quiz question data."""

    print("Generating Namibia administrative quiz data...")
    print()

    generated_datasets = []

    for config in DATASETS:
        questions = load_questions(config)

        generated_datasets.append(
            (config, questions)
        )

        print(
            f"{config['constant']}: "
            f"{len(questions):,} questions"
        )

    output = build_output(generated_datasets)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print()
    print("Namibia administrative quiz data generated.")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()