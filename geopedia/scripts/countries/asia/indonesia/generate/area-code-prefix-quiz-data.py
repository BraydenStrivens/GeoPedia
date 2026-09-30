"""
Generate GeoPedia quiz-question data for Indonesia's landline area-code prefixes.

The final processed area-code-prefix GeoJSON files are used as the source of
truth so the quiz question sets always match the values available on the maps.

Question formatting
-------------------
1-digit prefixes:
    answer "2" -> display "02-"

2-digit prefixes:
    answer "21" -> display "021"

The leading zero is included in displays because Indonesian landline area codes
are encountered with the trunk prefix 0 in GeoGuessr.

The 1-digit questions include a trailing "-" to make it clear that they are
prefixes rather than complete area codes. The 2-digit questions intentionally
omit the trailing "-" even though a small number of Indonesian area codes
continue for another digit.

Inputs
------
public/data/countries/indonesia/geojson/area-code-prefixes-1.geojson
public/data/countries/indonesia/geojson/area-code-prefixes-2.geojson

Output
------
src/quiz/quizzes/countries/asia/indonesia/data/area-code-prefixes.ts

Run from the GeoPedia project root:

    python scripts/countries/asia/indonesia/generate/area-code-prefix-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

GEOJSON_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "indonesia"
    / "geojson"
)

PREFIX_1_PATH = (
    GEOJSON_DIR
    / "area-code-prefixes-1.geojson"
)

PREFIX_2_PATH = (
    GEOJSON_DIR
    / "area-code-prefixes-2.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "asia"
    / "indonesia"
    / "data"
    / "area-code-prefixes.ts"
)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_prefixes(
    path: Path,
    property_name: str,
) -> list[str]:
    """Load and validate the unique prefix values from a GeoJSON file."""

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        geojson = json.load(
            file
        )

    features = geojson.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path} does not contain a valid GeoJSON feature array."
        )

    prefixes: list[str] = []

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        prefix = properties.get(
            property_name
        )

        if prefix is None:
            raise ValueError(
                f"A feature in {path.name} is missing "
                f"{property_name!r}."
            )

        prefix = str(
            prefix
        ).strip()

        if not prefix:
            raise ValueError(
                f"A feature in {path.name} has an empty "
                f"{property_name!r}."
            )

        if not prefix.isdigit():
            raise ValueError(
                f"Invalid {property_name} value in {path.name}: "
                f"{prefix!r}"
            )

        prefixes.append(
            prefix
        )

    if len(
        prefixes
    ) != len(
        set(
            prefixes
        )
    ):
        raise ValueError(
            f"{path.name} contains duplicate {property_name} values."
        )

    return sorted(
        prefixes,
        key=int,
    )


# ---------------------------------------------------------------------------
# TypeScript generation
# ---------------------------------------------------------------------------


def format_question(
    answer: str,
    display: str,
) -> str:
    """Format one FeatureQuizQuestion object."""

    return (
        f'  {{ answer: "{answer}", display: "{display}" }},'
    )


def build_typescript(
    prefix_1_values: list[str],
    prefix_2_values: list[str],
) -> str:
    """Build the generated TypeScript question-data module."""

    prefix_1_questions = "\n".join(
        format_question(
            prefix,
            f"0{prefix}-",
        )
        for prefix in prefix_1_values
    )

    prefix_2_questions = "\n".join(
        format_question(
            prefix,
            f"0{prefix}",
        )
        for prefix in prefix_2_values
    )

    return f'''/**
 * Generated quiz-question data for Indonesia's landline area-code prefixes.
 *
 * Source:
 * - /public/data/countries/indonesia/geojson/area-code-prefixes-1.geojson
 * - /public/data/countries/indonesia/geojson/area-code-prefixes-2.geojson
 *
 * Regenerate with:
 * python scripts/countries/asia/indonesia/generate/area-code-prefix-quiz-data.py
 *
 * Display convention:
 * - 1-digit prefix: answer "2" -> display "02-"
 * - 2-digit prefix: answer "21" -> display "021"
 *
 * The leading zero reflects how Indonesian landline area codes appear in-game.
 * The 1-digit set uses "-" to make the incomplete prefix explicit.
 */
import {{ FeatureQuizQuestion }} from "@/types/quiz";

export const INDONESIA_AREA_CODE_PREFIX_1_QUESTIONS: FeatureQuizQuestion[] = [
{prefix_1_questions}
];

export const INDONESIA_AREA_CODE_PREFIX_2_QUESTIONS: FeatureQuizQuestion[] = [
{prefix_2_questions}
];
'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate Indonesia's area-code-prefix quiz-question module."""

    print(
        "Generating Indonesia area-code-prefix quiz data..."
    )
    print()

    prefix_1_values = load_prefixes(
        PREFIX_1_PATH,
        "prefix_1",
    )

    prefix_2_values = load_prefixes(
        PREFIX_2_PATH,
        "prefix_2",
    )

    # Every 2-digit prefix must belong to a 1-digit prefix represented by
    # the broader prefix GeoJSON.
    prefix_1_set = set(
        prefix_1_values
    )

    missing_parent_prefixes = sorted(
        {
            prefix[0]
            for prefix in prefix_2_values
            if prefix[0] not in prefix_1_set
        },
        key=int,
    )

    if missing_parent_prefixes:
        raise ValueError(
            "2-digit prefixes reference missing 1-digit prefixes: "
            + ", ".join(
                missing_parent_prefixes
            )
        )

    typescript = build_typescript(
        prefix_1_values,
        prefix_2_values,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        typescript,
        encoding="utf-8",
    )

    print(
        f"1-digit questions: {len(prefix_1_values)}"
    )
    print(
        f"2-digit questions: {len(prefix_2_values)}"
    )

    print()
    print(
        "Values:"
    )
    print(
        "  1-digit: "
        + ", ".join(
            f"0{prefix}-"
            for prefix in prefix_1_values
        )
    )
    print(
        "  2-digit: "
        + ", ".join(
            f"0{prefix}"
            for prefix in prefix_2_values
        )
    )

    print()
    print(
        "Output:"
    )
    print(
        "  "
        + str(
            OUTPUT_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print(
        "Indonesia area-code-prefix quiz-data generation complete."
    )


if __name__ == "__main__":
    main()