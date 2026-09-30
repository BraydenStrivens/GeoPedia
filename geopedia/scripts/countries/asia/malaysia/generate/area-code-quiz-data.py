"""
Generates GeoPedia quiz-question data for Malaysia's area-code-prefix quizzes.

The finalized 1-digit and 2-digit area-code GeoJSON files are treated as the
source of truth. Duplicate geographic features sharing the same area code
produce only one quiz question.

For GeoPedia's naming, the digit count refers to the significant digits after
Malaysia's fixed leading 0:

- 03  -> 1-digit prefix, displayed as 03-
- 032 -> 2-digit prefix/full area code, displayed as 032

Inputs
------
public/data/countries/malaysia/geojson/area-code-prefixes-1.geojson
public/data/countries/malaysia/geojson/area-code-prefixes-2.geojson

Output
------
src/quiz/quizzes/countries/asia/malaysia/data/area-codes.ts

Run from the GeoPedia project root:

    python scripts/countries/asia/malaysia/generate/area-code-quiz-data.py
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

AREA_CODE_PREFIXES_1_PATH = (
    GEOJSON_DIRECTORY
    / "area-code-prefixes-1.geojson"
)

AREA_CODE_PREFIXES_2_PATH = (
    GEOJSON_DIRECTORY
    / "area-code-prefixes-2.geojson"
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
    / "area-codes.ts"
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


def extract_area_codes(
    data: dict[str, Any],
    expected_length: int,
    code_length: int,
) -> list[str]:
    """Extract, deduplicate, and validate area-code answers."""

    codes: set[str] = set()

    for feature in data["features"]:
        properties = feature.get(
            "properties",
            {},
        )

        area_code = properties.get(
            "area_code"
        )

        if not isinstance(
            area_code,
            str,
        ):
            raise ValueError(
                "Every feature must contain a string `area_code` property."
            )

        if (
            len(area_code) != code_length
            or not area_code.isdigit()
            or not area_code.startswith("0")
        ):
            raise ValueError(
                f"Invalid Malaysian area code: {area_code!r}"
            )

        codes.add(
            area_code
        )

    result = sorted(
        codes
    )

    if len(result) != expected_length:
        raise ValueError(
            f"Expected {expected_length} unique area codes "
            f"but found {len(result)}."
        )

    return result


# ---------------------------------------------------------------------------
# TypeScript generation
# ---------------------------------------------------------------------------


def format_question_array(
    export_name: str,
    codes: list[str],
    trailing_dash: bool,
) -> str:
    """Format one TypeScript FeatureQuizQuestion array."""

    lines = [
        f"export const {export_name}: FeatureQuizQuestion[] = [",
    ]

    for code in codes:
        if trailing_dash:
            lines.append(
                f'  {{ answer: "{code}", display: "{code}-" }},'
            )
        else:
            lines.append(
                f'  {{ answer: "{code}" }},'
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
    """Generate the complete area-code quiz-data module."""

    one_digit_array = format_question_array(
        "MALAYSIA_AREA_CODE_PREFIX_1_QUESTIONS",
        one_digit,
        trailing_dash=True,
    )

    two_digit_array = format_question_array(
        "MALAYSIA_AREA_CODE_PREFIX_2_QUESTIONS",
        two_digit,
        trailing_dash=False,
    )

    return f'''/**
 * Generated question data for Malaysia's area-code-prefix quizzes.
 *
 * Source:
 * public/data/countries/malaysia/geojson/area-code-prefixes-1.geojson
 * public/data/countries/malaysia/geojson/area-code-prefixes-2.geojson
 *
 * Regenerate with:
 * python scripts/countries/asia/malaysia/generate/area-code-quiz-data.py
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
    """Generate both Malaysia area-code question arrays."""

    print()
    print(
        "Generating Malaysia area-code quiz data..."
    )

    one_digit_data = load_geojson(
        AREA_CODE_PREFIXES_1_PATH
    )

    two_digit_data = load_geojson(
        AREA_CODE_PREFIXES_2_PATH
    )

    one_digit = extract_area_codes(
        one_digit_data,
        expected_length=7,
        code_length=2,
    )

    two_digit = extract_area_codes(
        two_digit_data,
        expected_length=52,
        code_length=3,
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
        "Malaysia area-code quiz-data generation complete."
    )


if __name__ == "__main__":
    main()