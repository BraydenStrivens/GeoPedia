"""
Generates the data used by Colombia's 4-digit postal-code quiz.

Source:
    public/data/countries/colombia/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/countries/south-america/colombia/data/postalCodes.ts

Municipality features may contain either one 4-digit postal prefix or multiple
prefixes. Bogotá is represented by one synthetic answer covering prefixes
1101 through 1120.
"""

from __future__ import annotations

import json
from pathlib import Path


SOURCE_PATH = Path(
    "public/data/countries/colombia/geojson/municipalities.geojson"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/south-america/colombia/data/postalCodes.ts"
)

EXPECTED_MUNICIPALITY_COUNT = 1_122

BOGOTA_POSTAL_ANSWER = "bogota-1101-1120"


def quote(value: str) -> str:
    """Serialize a string as a valid TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def load_features() -> list[dict]:
    """Load and validate Colombia's processed municipality GeoJSON."""
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"Source GeoJSON was not found: {SOURCE_PATH}"
        )

    data = json.loads(
        SOURCE_PATH.read_text(encoding="utf-8")
    )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Municipality GeoJSON is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Municipality GeoJSON is missing its features array."
        )

    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(features)}."
        )

    return features


def extract_postal_answers(
    features: list[dict],
) -> list[str]:
    """
    Return every distinct logical 4-digit postal-code answer.

    String properties contribute one answer. Array properties contribute one
    answer for each represented postal prefix.
    """
    answers: set[str] = set()

    for feature in features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "A municipality feature has invalid properties."
            )

        municipality_id = properties.get("id")
        value = properties.get("postal_code_4_digit")

        if isinstance(value, str):
            if not value:
                raise ValueError(
                    f"Municipality {municipality_id} has an empty "
                    "postal-code prefix."
                )

            answers.add(value)

        elif isinstance(value, list):
            for answer in value:
                if not isinstance(answer, str) or not answer:
                    raise ValueError(
                        f"Municipality {municipality_id} has an invalid "
                        "postal-code prefix."
                    )

                answers.add(answer)

        else:
            raise ValueError(
                f"Municipality {municipality_id} has an invalid "
                "postal_code_4_digit property."
            )

    if BOGOTA_POSTAL_ANSWER not in answers:
        raise ValueError(
            "Expected Bogotá synthetic postal answer was not found."
        )

    return sorted(
        answers,
        key=lambda answer: (
            answer == BOGOTA_POSTAL_ANSWER,
            answer,
        ),
    )


def get_display(answer: str) -> str:
    """Return the user-facing display text for one postal answer."""
    if answer == BOGOTA_POSTAL_ANSWER:
        return "1101–1120"

    if len(answer) != 4 or not answer.isdigit():
        raise ValueError(
            f"Unexpected postal answer: {answer}"
        )

    return f"{answer}--"


def create_source(
    answers: list[str],
) -> str:
    """Create the generated Colombia postal-code data module."""
    question_lines = "\n".join(
        "\n".join(
            [
                "  {",
                f"    answer: {quote(answer)},",
                f"    display: {quote(get_display(answer))},",
                "  },",
            ]
        )
        for answer in answers
    )

    return f'''/**
 * Generated from Colombia's processed municipality GeoJSON.
 *
 * Contains the questions used by Colombia's 4-digit postal-code quiz.
 * Bogotá is represented by one logical answer covering prefixes 1101–1120.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/colombia/generate/postal-codes-quiz-data.py
 */

import type {{ FeatureQuiz }} from "@/types/quiz";

export const COLOMBIA_POSTAL_CODE_4_QUESTIONS: FeatureQuiz["questions"] = [
{question_lines}
];
'''


def main() -> None:
    """Generate Colombia's postal-code quiz data."""
    print("Generating Colombia postal-code quiz data...\n")

    features = load_features()
    answers = extract_postal_answers(features)

    source = create_source(answers)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print(f"Questions: {len(answers):,}")
    print(f"Generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()