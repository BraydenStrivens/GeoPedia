"""
Generates the question data used by Canada's Census Divisions quiz.

Source:
    public/data/countries/canada/geojson/census-divisions.geojson

Output:
    src/quiz/quizzes/countries/north-america/canada/data/censusDivisions.ts

Each census division uses its Census Division Unique Identifier (CDUID) as
the answer so divisions remain uniquely identifiable even when names are
duplicated across provinces or territories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "canada"
    / "geojson"
    / "census-divisions.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "north-america"
    / "canada"
    / "data"
    / "censusDivisions.ts"
)

EXPECTED_FEATURE_COUNT = 293

REQUIRED_PROPERTIES = (
    "cduid",
    "name",
    "province",
)


def get_required_property(
    properties: dict[str, Any],
    property_name: str,
    feature_index: int,
) -> str:
    """Return one required non-empty string property."""
    value = properties.get(property_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f'Feature {feature_index} has invalid or missing '
            f'"{property_name}".'
        )

    return value.strip()


def should_include_province_in_display(
    name: str,
) -> bool:
    """
    Return whether a generic census division name needs its province or
    territory included in the visible question.
    """
    normalized_name = name.lower()

    return (
        normalized_name.startswith("division no.")
        or normalized_name.startswith("region ")
    )


def build_questions(
    features: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """
    Build census-division questions using CDUID as the stable answer value.
    """
    questions: list[dict[str, str]] = []
    seen_cduids: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {index} is missing a valid properties object."
            )

        values = {
            property_name: get_required_property(
                properties,
                property_name,
                index,
            )
            for property_name in REQUIRED_PROPERTIES
        }

        cduid = values["cduid"]
        name = values["name"]
        province = values["province"]

        if cduid in seen_cduids:
            raise ValueError(
                f'Duplicate CDUID "{cduid}" found in processed GeoJSON.'
            )

        seen_cduids.add(cduid)

        display = (
            f"{name}, {province}"
            if should_include_province_in_display(name)
            else name
        )

        questions.append(
            {
                "answer": cduid,
                "display": display,
            }
        )

    questions.sort(
        key=lambda question: question["display"]
    )

    return questions


def to_typescript_string(
    value: str,
) -> str:
    """Convert a Python string into a safe TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def generate_question_lines(
    questions: list[dict[str, str]],
) -> str:
    """Format the generated FeatureQuiz question objects."""
    return "\n".join(
        (
            "  { "
            f"answer: {to_typescript_string(question['answer'])}, "
            f"display: {to_typescript_string(question['display'])} "
            "},"
        )
        for question in questions
    )


def create_source(
    questions: list[dict[str, str]],
) -> str:
    """Create the generated TypeScript data module."""
    question_lines = generate_question_lines(
        questions
    )

    return f'''/**
 * Generated from Canada's processed census-division GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/canada/generate/census-divisions-quiz-data.py
 */

import type {{ FeatureQuiz }} from "@/types/quiz";

export const CANADA_CENSUS_DIVISION_QUESTIONS: FeatureQuiz["questions"] = [
{question_lines}
];
'''


def main() -> None:
    """Generate Canada's census-division quiz data."""
    print(
        "Generating Canada census-division quiz data...\n"
    )

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Census-division GeoJSON was not found: {INPUT_PATH}"
        )

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Input GeoJSON is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Input GeoJSON does not contain a valid features array."
        )

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} census divisions, "
            f"found {len(features)}."
        )

    questions = build_questions(
        features
    )

    if len(questions) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} generated questions, "
            f"found {len(questions)}."
        )

    source = create_source(
        questions
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print(
        f"Census divisions: {len(questions):,}"
    )
    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()