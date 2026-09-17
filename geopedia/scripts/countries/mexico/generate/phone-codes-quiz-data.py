"""
Generates the question data used by Mexico's telephone area-code quiz.

Source:
    public/data/countries/mexico/geojson/phone-codes.geojson

Output:
    src/quiz/quizzes/countries/north-america/mexico/data/phoneCodes.ts

Each distinct value in a feature's `area_codes` array becomes its own quiz
question. Geographic features may contain multiple valid answers, which are
handled by GeoPedia's multiple-answer feature mode.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
    / "countries"
    / "north-america"
    / "mexico"
    / "data"
    / "phoneCodes.ts"
)


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


def load_phone_codes() -> list[dict[str, Any]]:
    """Load and validate Mexico's processed phone-code GeoJSON."""
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


def collect_answers(
    features: list[dict[str, Any]],
) -> list[str]:
    """
    Collect and validate every distinct phone-code answer from the
    processed features.
    """
    answers: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Phone-code feature {index} has invalid properties."
            )

        area_codes = properties.get("area_codes")
        first_digit = properties.get("first_digit")
        state_ids = properties.get("state_ids")

        if (
            not isinstance(area_codes, list)
            or not area_codes
        ):
            raise ValueError(
                f"Phone-code feature {index} has invalid area_codes."
            )

        if first_digit not in EXPECTED_PREFIXES:
            raise ValueError(
                f"Feature {index} has invalid first_digit "
                f"{first_digit!r}."
            )

        if (
            not isinstance(state_ids, list)
            or not state_ids
        ):
            raise ValueError(
                f"Phone-code feature {index} has invalid state_ids."
            )

        if not all(
            isinstance(state_id, str)
            for state_id in state_ids
        ):
            raise ValueError(
                f"Phone-code feature {index} contains a non-string "
                "state ID."
            )

        invalid_state_ids = (
            set(state_ids)
            - EXPECTED_STATE_IDS
        )

        if invalid_state_ids:
            raise ValueError(
                f"Phone-code feature {index} has invalid state IDs: "
                f"{sorted(invalid_state_ids)}"
            )

        if len(set(state_ids)) != len(state_ids):
            raise ValueError(
                f"Phone-code feature {index} contains duplicate "
                "state IDs."
            )

        if len(set(area_codes)) != len(area_codes):
            raise ValueError(
                f"Phone-code feature {index} contains duplicate "
                "area codes."
            )

        for area_code in area_codes:
            if not isinstance(area_code, str):
                raise ValueError(
                    "Phone-code answer is not a string."
                )

            if not area_code.isdigit():
                raise ValueError(
                    f"Phone-code answer is not numeric: "
                    f"{area_code!r}."
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


def create_question_source(
    answer: str,
) -> str:
    """Create TypeScript source for one phone-code question."""
    return (
        f"  {{ answer: "
        f"{json.dumps(answer, ensure_ascii=False)} }},"
    )


def create_data_source(
    answers: list[str],
) -> str:
    """Create the generated TypeScript question-data module."""
    questions = "\n".join(
        create_question_source(answer)
        for answer in answers
    )

    return f'''/**
 * Generated from Mexico's processed telephone area-code GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/mexico/generate/phone-codes-quiz-data.py
 */

import type {{ FeatureQuiz }} from "@/types/quiz";

export const MEXICO_PHONE_CODE_QUESTIONS: FeatureQuiz["questions"] = [
{questions}
];
'''


def main() -> None:
    """Generate Mexico's telephone area-code quiz data."""
    print(
        "Generating Mexico phone-code quiz data...\n"
    )

    features = load_phone_codes()

    answers = collect_answers(
        features
    )

    source = create_data_source(
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

    represented_prefixes = {
        feature["properties"]["first_digit"]
        for feature in features
    }

    represented_state_ids = {
        state_id
        for feature in features
        for state_id in feature["properties"]["state_ids"]
    }

    multi_answer_feature_count = sum(
        1
        for feature in features
        if len(
            feature["properties"]["area_codes"]
        ) > 1
    )

    print(
        f"Geographic features:   {len(features):,}"
    )
    print(
        f"Questions:             {len(answers):,}"
    )
    print(
        f"Multi-answer features: {multi_answer_feature_count:,}"
    )
    print(
        f"First-digit groups:    {len(represented_prefixes):,}"
    )
    print(
        f"States represented:    {len(represented_state_ids):,}"
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()