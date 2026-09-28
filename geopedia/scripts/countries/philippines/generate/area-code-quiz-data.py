"""
Generate Philippines telephone area-code quiz-question data for GeoPedia.

This script reads the final public Philippines area-code GeoJSON datasets and
generates the TypeScript question arrays used by the area-code quizzes.

Inputs
------
    public/data/countries/philippines/geojson/
        area-codes.geojson
        area-code-prefixes.geojson

Output
------
    src/quiz/quizzes/countries/asia/philippines/data/
        area-codes.ts

Generated arrays
----------------
    PHILIPPINES_AREA_CODE_QUESTIONS
        One question for each complete domestic area code.

    PHILIPPINES_AREA_CODE_PREFIX_QUESTIONS
        One question for each one-digit area-code prefix group.

Domestic dialing format
-----------------------
Answers include the leading 0 used when dialing domestically:

    02
    032
    033
    ...
    088

Prefix questions use the prefix itself as the answer and append "-" to the
player-facing display to indicate that additional digits normally follow:

    answer "03" -> display "03-"
    answer "04" -> display "04-"

02 is the exception because 02 is itself a complete area code rather than the
prefix of codes such as 021 or 025. Its question therefore has no separate
display value:

    { answer: "02" }

Question arrays are explicitly typed as FeatureQuizQuestion[].

Run from the GeoPedia project root:

    python scripts/countries/philippines/generate/area-code-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

PUBLIC_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "philippines"
    / "geojson"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "asia"
    / "philippines"
    / "data"
)

AREA_CODES_PATH = (
    PUBLIC_DIRECTORY
    / "area-codes.geojson"
)

PREFIXES_PATH = (
    PUBLIC_DIRECTORY
    / "area-code-prefixes.geojson"
)

OUTPUT_PATH = (
    OUTPUT_DIRECTORY
    / "area-codes.ts"
)


# ---------------------------------------------------------------------------
# Expected data
# ---------------------------------------------------------------------------

EXPECTED_AREA_CODES = {
    "02",
    "032",
    "033",
    "034",
    "035",
    "036",
    "038",
    "042",
    "043",
    "044",
    "045",
    "046",
    "047",
    "048",
    "049",
    "052",
    "053",
    "054",
    "055",
    "056",
    "062",
    "063",
    "064",
    "065",
    "068",
    "072",
    "074",
    "075",
    "077",
    "078",
    "082",
    "083",
    "084",
    "085",
    "086",
    "087",
    "088",
}

EXPECTED_PREFIXES = {
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
}


# ---------------------------------------------------------------------------
# GeoJSON helpers
# ---------------------------------------------------------------------------


def load_feature_collection(
    path: Path,
) -> list[dict[str, Any]]:
    """Load and validate a GeoJSON FeatureCollection."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required GeoJSON not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if data.get(
        "type"
    ) != "FeatureCollection":
        raise ValueError(
            f"{path.name} is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path.name} has a malformed features array."
        )

    return features


def require_string(
    feature: dict[str, Any],
    property_name: str,
    *,
    label: str,
) -> str:
    """Read a required non-empty string from a feature's properties."""

    properties = feature.get(
        "properties"
    )

    if not isinstance(
        properties,
        dict,
    ):
        raise ValueError(
            f"{label} has malformed properties."
        )

    value = properties.get(
        property_name
    )

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{label} has non-string property {property_name!r}."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{label} has blank property {property_name!r}."
        )

    return value


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------


def extract_unique_values(
    features: list[dict[str, Any]],
    property_name: str,
    *,
    label: str,
) -> list[str]:
    """Extract, validate, and sort unique values from a GeoJSON property."""

    values: list[str] = []
    seen: set[str] = set()

    for feature_number, feature in enumerate(
        features,
        start=1,
    ):
        value = require_string(
            feature,
            property_name,
            label=f"{label} feature {feature_number:,}",
        )

        if value in seen:
            raise ValueError(
                f"{label}: duplicate value {value!r}."
            )

        seen.add(
            value
        )

        values.append(
            value
        )

    return sorted(
        values
    )


def validate_values(
    actual: list[str],
    expected: set[str],
    *,
    label: str,
) -> None:
    """Validate a generated answer set against its expected values."""

    actual_set = set(
        actual
    )

    if actual_set == expected:
        return

    missing = sorted(
        expected
        - actual_set
    )

    unexpected = sorted(
        actual_set
        - expected
    )

    raise ValueError(
        f"{label} set mismatch.\n"
        f"Missing: {missing}\n"
        f"Unexpected: {unexpected}"
    )


# ---------------------------------------------------------------------------
# TypeScript generation
# ---------------------------------------------------------------------------


def format_area_code_questions(
    area_codes: list[str],
) -> str:
    """Format complete area-code questions as TypeScript."""

    lines = [
        (
            "export const PHILIPPINES_AREA_CODE_QUESTIONS: "
            "FeatureQuizQuestion[] = ["
        ),
    ]

    for area_code in area_codes:
        lines.append(
            f'  {{ answer: "{area_code}" }},'
        )

    lines.append(
        "];"
    )

    return "\n".join(
        lines
    )


def format_prefix_questions(
    prefixes: list[str],
) -> str:
    """Format one-digit prefix questions as TypeScript."""

    lines = [
        (
            "export const PHILIPPINES_AREA_CODE_PREFIX_QUESTIONS: "
            "FeatureQuizQuestion[] = ["
        ),
    ]

    for prefix in prefixes:
        if prefix == "02":
            lines.append(
                '  { answer: "02" },'
            )

        else:
            lines.append(
                f'  {{ answer: "{prefix}", display: "{prefix}-" }},'
            )

    lines.append(
        "];"
    )

    return "\n".join(
        lines
    )


def generate_typescript(
    area_codes: list[str],
    prefixes: list[str],
) -> str:
    """Generate the complete area-codes.ts source file."""

    return f'''/**
 * Generated quiz-question data for the Philippines' telephone area codes.
 *
 * Complete area-code answers use domestic dialing format, including the
 * leading 0.
 *
 * Prefix questions append "-" to the display when the answer represents the
 * beginning of a family of area codes. 02 is already a complete area code and
 * therefore does not use a separate display value.
 *
 * Regenerate with:
 *
 *   python scripts/countries/philippines/generate/area-code-quiz-data.py
 */

import {{ FeatureQuizQuestion }} from "@/types/quiz";

{format_prefix_questions(prefixes)}

{format_area_code_questions(area_codes)}

'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Generating Philippines telephone area-code quiz data..."
    )
    print()

    area_code_features = load_feature_collection(
        AREA_CODES_PATH
    )

    prefix_features = load_feature_collection(
        PREFIXES_PATH
    )

    area_codes = extract_unique_values(
        area_code_features,
        "area_code",
        label="Area codes",
    )

    prefixes = extract_unique_values(
        prefix_features,
        "prefix_1",
        label="Area-code prefixes",
    )

    validate_values(
        area_codes,
        EXPECTED_AREA_CODES,
        label="Area codes",
    )

    validate_values(
        prefixes,
        EXPECTED_PREFIXES,
        label="Area-code prefixes",
    )

    if len(
        area_codes
    ) != 37:
        raise ValueError(
            f"Expected 37 area-code questions but found {len(area_codes):,}."
        )

    if len(
        prefixes
    ) != 7:
        raise ValueError(
            f"Expected 7 prefix questions but found {len(prefixes):,}."
        )

    typescript = generate_typescript(
        area_codes,
        prefixes,
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        typescript,
        encoding="utf-8",
    )

    print(
        f"Area-code questions: {len(area_codes):,}"
    )
    print(
        f"Prefix questions:    {len(prefixes):,}"
    )
    print()
    print(
        f"Output: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}"
    )
    print()
    print(
        "Philippines telephone area-code quiz data generated successfully."
    )


if __name__ == "__main__":
    main()