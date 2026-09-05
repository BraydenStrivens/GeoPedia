"""
Generates GeoPedia quiz definitions for US ZIP-code prefixes.

The quiz questions are generated directly from the processed GeoJSON maps,
ensuring that every quiz question corresponds to a geographic feature that
actually exists.

The displayed question uses hyphens to represent the remaining digits of a
full five-digit ZIP code:

    "1"   -> "1----"
    "34"  -> "34---"
    "234" -> "234--"

The underlying answer remains only the prefix so it can be matched directly
against the GeoJSON feature's `zip` property.
"""

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIRECTORY = Path("public/data")

QUIZ_DIRECTORY = Path(
    "src/quiz/quizzes/usa"
)


QUIZ_CONFIGS = {
    1: {
        "id": "us-zip-1",
        "name": "US 1-Digit ZIP Codes",
        "map_id": "us-zip-1",
        "variable_name": "usZip1Quiz",
    },
    2: {
        "id": "us-zip-2",
        "name": "US 2-Digit ZIP Codes",
        "map_id": "us-zip-2",
        "variable_name": "usZip2Quiz",
    },
    3: {
        "id": "us-zip-3",
        "name": "US 3-Digit ZIP Codes",
        "map_id": "us-zip-3",
        "variable_name": "usZip3Quiz",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_prefixes(prefix_length):
    """
    Loads and sorts the ZIP prefixes from a processed GeoJSON file.
    """
    input_file = (
        DATA_DIRECTORY
        / f"us-zip-{prefix_length}.geojson"
    )

    with input_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    prefixes = {
        str(
            feature["properties"]["zip"]
        )
        for feature in data["features"]
    }

    return sorted(prefixes)


def create_display(
    prefix,
):
    """
    Converts a ZIP prefix into its five-digit display representation.
    """
    remaining_digits = 5 - len(prefix)

    return (
        prefix
        + "-" * remaining_digits
    )


def generate_question_lines(
    prefixes,
):
    """
    Generates the TypeScript question objects for a quiz.
    """
    lines = []

    for prefix in prefixes:
        display = create_display(
            prefix
        )

        lines.append(
            f'    {{ answer: "{prefix}", '
            f'display: "{display}" }},'
        )

    return "\n".join(lines)


def generate_quiz(
    prefix_length,
):
    """
    Generates one TypeScript ZIP-prefix quiz definition.
    """
    config = QUIZ_CONFIGS[
        prefix_length
    ]

    prefixes = load_prefixes(
        prefix_length
    )

    question_lines = (
        generate_question_lines(
            prefixes
        )
    )

    output = f'''/**
 * Defines the United States {prefix_length}-digit ZIP-code prefix quiz.
 *
 * Each question represents the first {prefix_length} digit{"s" if prefix_length > 1 else ""}
 * of a five-digit ZIP code. The remaining digits are displayed as hyphens
 * so the user can see that the question represents a ZIP-code prefix rather
 * than a complete ZIP code.
 */

import type {{ Quiz }} from "@/types/quiz";

/**
 * Quiz definition for identifying US {prefix_length}-digit ZIP-code regions.
 */
export const {config["variable_name"]}: Quiz = {{
  id: "{config["id"]}",
  name: "{config["name"]}",
  mapId: "{config["map_id"]}",
  answerProperty: "zip",
  answerType: "single",

  questions: [
{question_lines}
  ],
}};
'''

    output_file = (
        QUIZ_DIRECTORY
        / (
            config["variable_name"]
            + ".ts"
        )
    )

    output_file.write_text(
        output,
        encoding="utf-8",
    )

    print(
        f"Generated "
        f"{len(prefixes)} questions: "
        f"{output_file}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    QUIZ_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    for prefix_length in (
        1,
        2,
        3,
    ):
        generate_quiz(
            prefix_length
        )


if __name__ == "__main__":
    main()