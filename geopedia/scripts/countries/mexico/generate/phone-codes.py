"""
Generate GeoPedia's Mexico Phone Codes quiz configuration.

Source
------
    public/data/countries/mexico/geojson/phone-codes.geojson

Output
------
    src/quiz/quizzes/mexico/mexicoPhoneCodesQuiz.ts

Each distinct value in a feature's `area_codes` array becomes its own quiz
question.

For example, a geographic feature containing:

    "area_codes": ["55", "56"]

produces two questions:

    { answer: "55" }
    { answer: "56" }

Both answers still resolve to the same geographic feature because the quiz uses
GeoPedia's multiple-answer feature mode.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

SOURCE_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "mexico"
    / "geojson"
    / "phone-codes.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "mexico"
    / "mexicoPhoneCodesQuiz.ts"
)


# ---------------------------------------------------------------------------
# Dataset expectations
# ---------------------------------------------------------------------------

EXPECTED_FEATURE_COUNT = 399
EXPECTED_ANSWER_COUNT = 400

EXPECTED_PREFIXES = {
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
}

EXPECTED_STATE_IDS = {
    f"{state_id:02d}"
    for state_id in range(1, 33)
}


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------


def load_phone_codes() -> list[dict[str, Any]]:
    """
    Load and validate the processed Mexico phone-code features.
    """

    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            "Missing processed Mexico phone-code GeoJSON:\n"
            f"  {SOURCE_PATH}"
        )

    with SOURCE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Mexico phone-code GeoJSON is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Mexico phone-code GeoJSON has no feature list."
        )

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            "Unexpected Mexico phone-code feature count: "
            f"expected {EXPECTED_FEATURE_COUNT}, "
            f"found {len(features)}."
        )

    return features


# ---------------------------------------------------------------------------
# Question extraction
# ---------------------------------------------------------------------------


def collect_answers(
    features: list[dict[str, Any]],
) -> list[str]:
    """
    Collect every distinct phone-code answer from the processed features.
    """

    answers: set[str] = set()

    for feature in features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "Phone-code feature has invalid properties."
            )

        area_codes = properties.get("area_codes")
        first_digit = properties.get("first_digit")
        state_ids = properties.get("state_ids")

        if (
            not isinstance(area_codes, list)
            or not area_codes
        ):
            raise ValueError(
                "Phone-code feature has invalid area_codes."
            )

        if first_digit not in EXPECTED_PREFIXES:
            raise ValueError(
                f"Feature has invalid first_digit {first_digit!r}."
            )

        if (
            not isinstance(state_ids, list)
            or not state_ids
        ):
            raise ValueError(
                "Phone-code feature has invalid state_ids."
            )

        invalid_state_ids = (
            set(state_ids)
            - EXPECTED_STATE_IDS
        )

        if invalid_state_ids:
            raise ValueError(
                "Phone-code feature has invalid state IDs: "
                f"{sorted(invalid_state_ids)}"
            )

        for area_code in area_codes:
            if not isinstance(area_code, str):
                raise ValueError(
                    "Phone-code answer is not a string."
                )

            if not area_code.isdigit():
                raise ValueError(
                    f"Phone-code answer is not numeric: {area_code!r}."
                )

            if area_code[0] != first_digit:
                raise ValueError(
                    f"Phone-code answer {area_code!r} does not match "
                    f"first_digit {first_digit!r}."
                )

            if area_code in answers:
                raise ValueError(
                    "Duplicate phone-code quiz answer: "
                    f"{area_code}"
                )

            answers.add(area_code)

    if len(answers) != EXPECTED_ANSWER_COUNT:
        raise ValueError(
            "Unexpected distinct phone-code answer count: "
            f"expected {EXPECTED_ANSWER_COUNT}, "
            f"found {len(answers)}."
        )

    return sorted(
        answers,
        key=int,
    )


# ---------------------------------------------------------------------------
# TypeScript generation
# ---------------------------------------------------------------------------


def create_question_source(
    answer: str,
) -> str:
    """
    Create TypeScript source for one phone-code question.
    """

    return f'  {{ answer: "{answer}" }},'


def create_quiz_source(
    answers: list[str],
) -> str:
    """
    Create the complete Mexico Phone Codes quiz TypeScript module.
    """

    questions = "\n".join(
        create_question_source(answer)
        for answer in answers
    )

    return f'''/**
 * AUTO-GENERATED FILE.
 *
 * Generated by:
 *
 *   scripts/countries/mexico/generate/phone-codes.py
 *
 * Do not edit the question list manually. Update the processed Mexico
 * phone-code data and rerun the generator instead.
 */

import {{ MEXICO_STATE_NAMES_BY_ID }} from "@/constants/mexicoSubdivisions";
import type {{ FeatureQuiz }} from "@/types/quiz";

const MEXICO_PHONE_CODE_QUESTIONS: FeatureQuiz["questions"] = [
{questions}
];

const MEXICO_PHONE_CODES_DESCRIPTION =
  `Learn all ${{MEXICO_PHONE_CODE_QUESTIONS.length}} Mexican phone codes, with filtering options to practice by first digit, state, or any desired subset.`;

/**
 * Quiz definition for identifying Mexico's geographic telephone-code regions.
 *
 * Geographic features may contain multiple valid phone-code answers. Each
 * individual code remains a separate quiz question while shared geographic
 * features use GeoPedia's multiple-answer feature behavior.
 */
export const mexicoPhoneCodesQuiz: FeatureQuiz = {{
  id: "mexico-phone-codes",
  name: "Mexico Phone Codes",
  description: MEXICO_PHONE_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-phone-codes",

  answerProperty: "area_codes",
  answerType: "multiple",

  grouping: {{
    properties: [
      {{
        property: "first_digit",
        label: "First Digit",
        valueType: "string",
      }},
      {{
        property: "state_ids",
        label: "State",
        valueType: "string-array",
        valueLabels: MEXICO_STATE_NAMES_BY_ID,
      }},
    ],
  }},

  questions: MEXICO_PHONE_CODE_QUESTIONS,
}};
'''


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Generate the Mexico Phone Codes quiz configuration.
    """

    print("Mexico phone-code quiz generator")
    print("-------------------------------")
    print(f"Source: {SOURCE_PATH}")
    print()

    features = load_phone_codes()

    print(
        f"✓ Loaded exactly {len(features):,} "
        "phone-code geographic features."
    )

    answers = collect_answers(features)

    print(
        f"✓ Found exactly {len(answers):,} "
        "distinct phone-code quiz answers."
    )

    source = create_quiz_source(
        answers
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print()
    print("✓ Generated quiz:")
    print(f"  {OUTPUT_PATH}")


if __name__ == "__main__":
    main()