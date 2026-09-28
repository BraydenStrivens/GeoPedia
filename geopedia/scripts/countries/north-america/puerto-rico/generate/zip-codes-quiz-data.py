"""
Generate Puerto Rico's postal-code quiz data for GeoPedia.

Inputs:
    public/data/countries/puerto-rico/geojson/zip-code-prefixes.geojson
    public/data/countries/puerto-rico/geojson/zip-codes.geojson

Output:
    src/quiz/quizzes/countries/north-america/puerto-rico/data/postalCodes.ts

The generated data contains question sets for Puerto Rico's 3-digit ZIP-code
prefixes and full 5-digit ZIP codes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

GEOJSON_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
)

PREFIXES_PATH = (
    GEOJSON_DIRECTORY
    / "zip-code-prefixes.geojson"
)

ZIP_CODES_PATH = (
    GEOJSON_DIRECTORY
    / "zip-codes.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "north-america"
    / "puerto-rico"
    / "data"
    / "postalCodes.ts"
)


EXPECTED_PREFIXES = {
    "006",
    "007",
    "009",
}

EXPECTED_ZIP_CODE_COUNT = 132


def load_features(
    path: Path,
) -> list[dict[str, Any]]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file does not exist:\n  {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected a GeoJSON FeatureCollection: {path}"
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"GeoJSON contains no valid features array: {path}"
        )

    return features


def read_property_values(
    features: list[dict[str, Any]],
    property_name: str,
) -> list[str]:
    """Read unique non-empty string values from a GeoJSON property."""
    values: list[str] = []

    for index, feature in enumerate(
        features,
        start=1,
    ):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {index} has invalid properties."
            )

        value = str(
            properties.get(
                property_name,
                "",
            )
        ).strip()

        if not value:
            raise ValueError(
                f"Feature {index} is missing {property_name!r}."
            )

        values.append(value)

    if len(values) != len(set(values)):
        raise ValueError(
            f"Duplicate {property_name!r} values found."
        )

    return sorted(values)


def load_prefixes() -> list[str]:
    """Load and validate Puerto Rico's 3-digit ZIP-code prefixes."""
    features = load_features(
        PREFIXES_PATH
    )

    prefixes = read_property_values(
        features,
        "prefix_3",
    )

    actual_prefixes = set(prefixes)

    if actual_prefixes != EXPECTED_PREFIXES:
        raise ValueError(
            "Unexpected 3-digit ZIP-code prefixes. "
            f"Expected {sorted(EXPECTED_PREFIXES)}, "
            f"found {prefixes}."
        )

    for prefix in prefixes:
        if len(prefix) != 3 or not prefix.isdigit():
            raise ValueError(
                f"Invalid 3-digit ZIP-code prefix: {prefix!r}"
            )

    return prefixes


def load_zip_codes() -> list[str]:
    """Load and validate Puerto Rico's full 5-digit ZIP codes."""
    features = load_features(
        ZIP_CODES_PATH
    )

    if len(features) != EXPECTED_ZIP_CODE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ZIP_CODE_COUNT} ZIP-code features, "
            f"found {len(features)}."
        )

    zip_codes = read_property_values(
        features,
        "zip_code",
    )

    if len(zip_codes) != EXPECTED_ZIP_CODE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ZIP_CODE_COUNT} unique ZIP codes, "
            f"found {len(zip_codes)}."
        )

    for zip_code in zip_codes:
        if len(zip_code) != 5 or not zip_code.isdigit():
            raise ValueError(
                f"Invalid 5-digit ZIP code: {zip_code!r}"
            )

        if zip_code[:3] not in EXPECTED_PREFIXES:
            raise ValueError(
                f"ZIP code {zip_code!r} has unexpected "
                f"3-digit prefix {zip_code[:3]!r}."
            )

    return zip_codes


def ts_string(
    value: str,
) -> str:
    """Return a safely encoded TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_prefix_questions(
    prefixes: list[str],
) -> str:
    """Render the 3-digit ZIP-code prefix questions."""
    lines = [
        "export const PUERTO_RICO_ZIP_CODE_PREFIX_QUESTIONS = [",
    ]

    for prefix in prefixes:
        lines.append(
            "  { "
            f"answer: {ts_string(prefix)}, "
            f"display: {ts_string(f'{prefix}--')} "
            "},"
        )

    lines.extend(
        [
            "];",
            "",
        ]
    )

    return "\n".join(lines)


def render_zip_code_questions(
    zip_codes: list[str],
) -> str:
    """Render the full 5-digit ZIP-code questions."""
    lines = [
        "export const PUERTO_RICO_ZIP_CODE_QUESTIONS = [",
    ]

    for zip_code in zip_codes:
        lines.append(
            f"  {{ answer: {ts_string(zip_code)} }},"
        )

    lines.extend(
        [
            "];",
            "",
        ]
    )

    return "\n".join(lines)


def create_source(
    prefixes: list[str],
    zip_codes: list[str],
) -> str:
    """Create the generated TypeScript postal-code data module."""
    return f'''/**
 * Generated postal-code quiz data for Puerto Rico.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/puerto-rico/generate/postal-codes-quiz-data.py
 */

{render_prefix_questions(prefixes)}{render_zip_code_questions(zip_codes)}'''


def main() -> None:
    """Generate Puerto Rico's postal-code quiz data."""
    print(
        "Generating Puerto Rico postal-code quiz data...\n"
    )

    prefixes = load_prefixes()
    zip_codes = load_zip_codes()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            prefixes,
            zip_codes,
        ),
        encoding="utf-8",
    )

    print(
        f"3-digit ZIP prefixes: {len(prefixes):,}"
    )
    print(
        f"5-digit ZIP codes:    {len(zip_codes):,}"
    )
    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()