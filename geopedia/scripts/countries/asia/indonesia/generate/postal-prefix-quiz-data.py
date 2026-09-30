"""
Generate Indonesia postal-prefix quiz question data.

Purpose
-------
Reads GeoPedia's processed Indonesia postal-prefix GeoJSON files and generates
the TypeScript question arrays used by the 1-digit and 2-digit postal-prefix
quizzes.

Answers store only the significant prefix digits. Display labels show the
prefix in the context of Indonesia's 5-digit postal codes:

    2   -> 2----
    23  -> 23---

Inputs
------
    public/data/countries/indonesia/geojson/postal-prefixes-1.geojson
    public/data/countries/indonesia/geojson/postal-prefixes-2.geojson

Output
------
    src/quiz/quizzes/countries/asia/indonesia/data/postal-prefixes.ts

Run from the GeoPedia project root:

    python scripts/countries/asia/indonesia/generate/postal-prefix-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[5]

GEOJSON_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "indonesia"
    / "geojson"
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
    / "postal-prefixes.ts"
)

PREFIX_1_PATH = (
    GEOJSON_DIR
    / "postal-prefixes-1.geojson"
)

PREFIX_2_PATH = (
    GEOJSON_DIR
    / "postal-prefixes-2.geojson"
)

EXPECTED_PREFIX_1_COUNT = 9
EXPECTED_PREFIX_2_COUNT = 83


def load_prefixes(
    path: Path,
    property_name: str,
) -> list[str]:
    """Load, validate, and numerically sort prefix values."""

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    prefixes: list[str] = []

    for feature in data[
        "features"
    ]:
        prefix = str(
            feature[
                "properties"
            ][
                property_name
            ]
        )

        if not prefix.isdigit():
            raise ValueError(
                f"Invalid {property_name}: {prefix!r}"
            )

        prefixes.append(
            prefix
        )

    if len(prefixes) != len(
        set(
            prefixes
        )
    ):
        raise ValueError(
            f"Duplicate {property_name} values found."
        )

    return sorted(
        prefixes,
        key=int,
    )


def question_lines(
    prefixes: list[str],
) -> list[str]:
    """Create TypeScript FeatureQuizQuestion entries."""

    lines: list[str] = []

    for prefix in prefixes:
        missing_digits = (
            5
            - len(
                prefix
            )
        )

        display = (
            prefix
            + "-" * missing_digits
        )

        lines.append(
            f'  {{ answer: "{prefix}", display: "{display}" }},'
        )

    return lines


def main() -> None:
    """Generate the postal-prefix TypeScript question data."""

    prefix_1 = load_prefixes(
        PREFIX_1_PATH,
        "prefix_1",
    )

    prefix_2 = load_prefixes(
        PREFIX_2_PATH,
        "prefix_2",
    )

    if len(prefix_1) != EXPECTED_PREFIX_1_COUNT:
        raise ValueError(
            "Unexpected 1-digit prefix count: "
            f"expected {EXPECTED_PREFIX_1_COUNT}, "
            f"got {len(prefix_1)}."
        )

    if len(prefix_2) != EXPECTED_PREFIX_2_COUNT:
        raise ValueError(
            "Unexpected 2-digit prefix count: "
            f"expected {EXPECTED_PREFIX_2_COUNT}, "
            f"got {len(prefix_2)}."
        )

    lines = [
        "/**",
        " * Quiz question data for Indonesia's postal-code prefix quizzes.",
        " *",
        " * Generated from GeoPedia's processed postal-prefix GeoJSON.",
        " * Answers contain only the significant prefix digits, while display",
        " * labels show their position within Indonesia's 5-digit postal codes.",
        " *",
        " * Regenerate with:",
        " *",
        " *   python scripts/countries/asia/indonesia/generate/postal-prefix-quiz-data.py",
        " */",
        "",
        'import { FeatureQuizQuestion } from "@/types/quiz";',
        "",
        "export const INDONESIA_POSTAL_PREFIX_1_QUESTIONS: FeatureQuizQuestion[] = [",
        *question_lines(
            prefix_1
        ),
        "];",
        "",
        "export const INDONESIA_POSTAL_PREFIX_2_QUESTIONS: FeatureQuizQuestion[] = [",
        *question_lines(
            prefix_2
        ),
        "];",
        "",
    ]

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )

    print(
        "Indonesia postal-prefix quiz data generated."
    )
    print(
        f"1-digit questions: {len(prefix_1):,}"
    )
    print(
        f"2-digit questions: {len(prefix_2):,}"
    )
    print(
        OUTPUT_PATH.relative_to(
            PROJECT_ROOT
        )
    )


if __name__ == "__main__":
    main()