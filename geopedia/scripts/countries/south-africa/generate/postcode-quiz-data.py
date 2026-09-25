"""
Generate South Africa postcode quiz question data.

The generator reads the final runtime GeoJSON datasets for South Africa's
one-, two-, three-, and four-digit postcode quizzes and creates the TypeScript
question arrays consumed by their quiz configs.

Prefix questions use the raw numeric prefix as their answer while displaying
the prefix in four-digit postcode form with unknown trailing digits represented
by hyphens. For example:

    1-digit:  "2"   -> "2---"
    2-digit:  "21"  -> "21--"
    3-digit:  "219" -> "219-"
    4-digit:  "2192"

Reading the public GeoJSON files ensures every generated quiz answer has a
corresponding runtime map feature.

Inputs:

    public/data/countries/south-africa/geojson/postcodes-1.geojson
    public/data/countries/south-africa/geojson/postcodes-2.geojson
    public/data/countries/south-africa/geojson/postcodes-3.geojson
    public/data/countries/south-africa/geojson/postcodes-4.geojson

Output:

    src/quiz/quizzes/countries/africa/south-africa/data/postcodes.ts

Run from the GeoPedia project root:

    python scripts/countries/south-africa/generate/postcode-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GEOJSON_DIRECTORY = Path(
    "public/data/countries/south-africa/geojson"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/africa/south-africa/data/"
    "postcodes.ts"
)

LEVELS = (
    (
        1,
        "prefix_1",
        "SOUTH_AFRICA_POSTCODES_1_QUIZ_QUESTIONS",
    ),
    (
        2,
        "prefix_2",
        "SOUTH_AFRICA_POSTCODES_2_QUIZ_QUESTIONS",
    ),
    (
        3,
        "prefix_3",
        "SOUTH_AFRICA_POSTCODES_3_QUIZ_QUESTIONS",
    ),
    (
        4,
        "postcode",
        "SOUTH_AFRICA_POSTCODES_4_QUIZ_QUESTIONS",
    ),
)


def load_feature_collection(
    path: Path,
) -> dict[str, Any]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} has no valid features array."
        )

    return data


def read_answers(
    digits: int,
    property_name: str,
) -> list[str]:
    """Read, validate, and sort quiz answers for one postcode level."""
    path = (
        GEOJSON_DIRECTORY
        / f"postcodes-{digits}.geojson"
    )

    data = load_feature_collection(
        path
    )

    answers: list[str] = []
    seen: set[str] = set()

    for feature in data["features"]:
        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"{path} contains a feature "
                "without valid properties."
            )

        answer = properties.get(
            property_name
        )

        if (
            not isinstance(answer, str)
            or len(answer) != digits
            or not answer.isdigit()
        ):
            raise ValueError(
                f"Invalid {digits}-digit postcode "
                f"value: {answer!r}"
            )

        if answer in seen:
            raise ValueError(
                f"Duplicate {property_name}: "
                f"{answer}"
            )

        seen.add(
            answer
        )

        answers.append(
            answer
        )

    answers.sort()

    return answers


def display_value(
    answer: str,
    digits: int,
) -> str | None:
    """
    Return the displayed postcode pattern for a prefix.

    Complete four-digit postcodes need no separate display value.
    """
    if digits == 4:
        return None

    return (
        answer
        + "-"
        * (4 - digits)
    )


def format_question_array(
    constant_name: str,
    answers: list[str],
    digits: int,
) -> str:
    """Format one generated FeatureQuizQuestion array."""
    lines = [
        (
            f"export const {constant_name}: "
            "FeatureQuizQuestion[] = ["
        )
    ]

    for answer in answers:
        display = display_value(
            answer,
            digits,
        )

        if display is None:
            lines.append(
                f'  {{ answer: "{answer}" }},'
            )
        else:
            lines.append(
                f'  {{ answer: "{answer}", '
                f'display: "{display}" }},'
            )

    lines.append(
        "];"
    )

    return "\n".join(
        lines
    )


def main() -> None:
    """Generate all South Africa postcode question arrays."""
    sections: list[str] = []

    print(
        "Generating South Africa postcode quiz data..."
    )

    for (
        digits,
        property_name,
        constant_name,
    ) in LEVELS:
        answers = read_answers(
            digits,
            property_name,
        )

        print(
            f"{digits}-digit questions: "
            f"{len(answers):,}"
        )

        sections.append(
            format_question_array(
                constant_name,
                answers,
                digits,
            )
        )

    content = (
        "/**\n"
        " * Generated South Africa postcode quiz questions.\n"
        " *\n"
        " * Prefix answers retain their raw numeric value while their display\n"
        " * represents unknown trailing postcode digits with hyphens.\n"
        " *\n"
        " * DO NOT EDIT MANUALLY.\n"
        " *\n"
        " * Regenerate with:\n"
        " * python scripts/countries/south-africa/generate/"
        "postcode-quiz-data.py\n"
        " */\n\n"
        'import type { FeatureQuizQuestion } from "@/types/quiz";\n\n'
        + "\n\n".join(
            sections
        )
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

    print()
    print(
        f"Wrote {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()