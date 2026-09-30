"""
Generates GeoPedia quiz-question data for Malaysia's postal-code-prefix quizzes.

The finalized 1-digit and 2-digit postal-prefix GeoJSON files are treated as
the source of truth. Questions are generated directly from their `post_code`
properties so quiz answers always remain synchronized with the map data.

Inputs
------
public/data/countries/malaysia/geojson/postal-prefixes-1.geojson
public/data/countries/malaysia/geojson/postal-prefixes-2.geojson

Output
------
src/quiz/quizzes/countries/asia/malaysia/data/postal-codes.ts

Run from the GeoPedia project root:

    python scripts/countries/asia/malaysia/generate/postal-code-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

GEOJSON_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "malaysia"
    / "geojson"
)

POSTAL_PREFIXES_1_PATH = (
    GEOJSON_DIRECTORY
    / "postal-prefixes-1.geojson"
)

POSTAL_PREFIXES_2_PATH = (
    GEOJSON_DIRECTORY
    / "postal-prefixes-2.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "asia"
    / "malaysia"
    / "data"
    / "postal-codes.ts"
)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    """Load one finalized GeoJSON file."""

    if not path.exists():
        raise FileNotFoundError(
            f"Missing GeoJSON file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected FeatureCollection: {path}"
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"GeoJSON has no valid features array: {path}"
        )

    return data


# ---------------------------------------------------------------------------
# Question extraction
# ---------------------------------------------------------------------------


def extract_post_codes(
    data: dict[str, Any],
    expected_length: int,
    digit_count: int,
) -> list[str]:
    """Extract and validate unique postal-code prefixes."""

    prefixes: list[str] = []

    for feature in data["features"]:
        properties = feature.get(
            "properties",
            {},
        )

        post_code = properties.get(
            "post_code"
        )

        if not isinstance(
            post_code,
            str,
        ):
            raise ValueError(
                "Every feature must contain a string `post_code` property."
            )

        if (
            len(post_code) != digit_count
            or not post_code.isdigit()
        ):
            raise ValueError(
                f"Invalid {digit_count}-digit postal prefix: {post_code!r}"
            )

        prefixes.append(
            post_code
        )

    if len(prefixes) != expected_length:
        raise ValueError(
            f"Expected {expected_length} {digit_count}-digit prefixes "
            f"but found {len(prefixes)}."
        )

    if len(set(prefixes)) != len(prefixes):
        raise ValueError(
            f"Duplicate {digit_count}-digit postal prefixes found."
        )

    return sorted(
        prefixes
    )


# ---------------------------------------------------------------------------
# TypeScript generation
# ---------------------------------------------------------------------------


def format_question_array(
    export_name: str,
    prefixes: list[str],
) -> str:
    remaining_digits = "---"
    
    if export_name == "MALAYSIA_POSTAL_PREFIX_1_QUESTIONS":
        remaining_digits = "----"
    
    """Format one TypeScript FeatureQuizQuestion array."""

    lines = [
        f"export const {export_name}: FeatureQuizQuestion[] = [",
    ]

    for prefix in prefixes:
        lines.append(
            f'  {{ answer: "{prefix}", display: "{prefix}{remaining_digits}" }},'
        )

    lines.append(
        "];"
    )

    return "\n".join(
        lines
    )


def generate_typescript(
    one_digit: list[str],
    two_digit: list[str],
) -> str:
    """Generate the complete postal-code quiz-data module."""

    one_digit_array = format_question_array(
        "MALAYSIA_POSTAL_PREFIX_1_QUESTIONS",
        one_digit,
    )

    two_digit_array = format_question_array(
        "MALAYSIA_POSTAL_PREFIX_2_QUESTIONS",
        two_digit,
    )

    return f'''/**
 * Generated question data for Malaysia's postal-code-prefix quizzes.
 *
 * Source:
 * public/data/countries/malaysia/geojson/postal-prefixes-1.geojson
 * public/data/countries/malaysia/geojson/postal-prefixes-2.geojson
 *
 * Regenerate with:
 * python scripts/countries/asia/malaysia/generate/postal-code-quiz-data.py
 *
 * Do not edit this file manually.
 */

import {{ FeatureQuizQuestion }} from "@/types/quiz";

{one_digit_array}

{two_digit_array}
'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate both Malaysia postal-prefix question arrays."""

    print()
    print(
        "Generating Malaysia postal-code quiz data..."
    )

    one_digit_data = load_geojson(
        POSTAL_PREFIXES_1_PATH
    )

    two_digit_data = load_geojson(
        POSTAL_PREFIXES_2_PATH
    )

    one_digit = extract_post_codes(
        one_digit_data,
        expected_length=10,
        digit_count=1,
    )

    two_digit = extract_post_codes(
        two_digit_data,
        expected_length=83,
        digit_count=2,
    )

    output = generate_typescript(
        one_digit,
        two_digit,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print()
    print(
        f"1-digit questions: {len(one_digit):,}"
    )
    print(
        f"2-digit questions: {len(two_digit):,}"
    )

    print()
    print(
        "Output: "
        + str(
            OUTPUT_PATH.relative_to(
                PROJECT_ROOT
            )
        )
    )

    print()
    print(
        "Malaysia postal-code quiz-data generation complete."
    )


if __name__ == "__main__":
    main()