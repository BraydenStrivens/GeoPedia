"""
Generates the question data used by GeoPedia's United States ZIP-code
prefix quizzes.

Sources:
    public/data/countries/usa/geojson/zip-1.geojson
    public/data/countries/usa/geojson/zip-2.geojson
    public/data/countries/usa/geojson/zip-3.geojson

Output:
    src/quiz/quizzes/countries/north-america/usa/data/zipCodes.ts

Each question represents a one-, two-, or three-digit ZIP-code prefix.
The visible question pads the remaining positions of a five-digit ZIP code
with hyphens while the underlying answer remains the raw prefix.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

DATA_DIRECTORY = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "usa"
    / "geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "countries"
    / "north-america"
    / "usa"
    / "data"
    / "zipCodes.ts"
)


PREFIX_LENGTHS = (
    1,
    2,
    3,
)

CONSTANT_NAMES = {
    1: "US_ZIP_1_DIGIT_QUESTIONS",
    2: "US_ZIP_2_DIGIT_QUESTIONS",
    3: "US_ZIP_3_DIGIT_QUESTIONS",
}


def load_features(
    prefix_length: int,
) -> list[dict[str, Any]]:
    """Load and validate one processed US ZIP-prefix GeoJSON."""
    input_path = (
        DATA_DIRECTORY
        / f"zip-{prefix_length}.geojson"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            "Missing processed US ZIP-prefix GeoJSON:\n"
            f"  {input_path}"
        )

    with input_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"US {prefix_length}-digit ZIP-prefix GeoJSON "
            "is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"US {prefix_length}-digit ZIP-prefix GeoJSON "
            "does not contain a feature list."
        )

    if not features:
        raise ValueError(
            f"US {prefix_length}-digit ZIP-prefix GeoJSON "
            "contains no features."
        )

    return features


def collect_prefixes(
    features: list[dict[str, Any]],
    prefix_length: int,
) -> list[str]:
    """Collect and validate the ZIP prefixes for one quiz."""
    prefixes: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"ZIP-prefix feature {index} has invalid properties."
            )

        prefix = properties.get("zip")

        if isinstance(prefix, int):
            prefix = str(prefix)

        if not isinstance(prefix, str):
            raise ValueError(
                f"ZIP-prefix feature {index} has an invalid zip value."
            )

        if not prefix.isdigit():
            raise ValueError(
                f"ZIP prefix {prefix!r} is not numeric."
            )

        if len(prefix) != prefix_length:
            raise ValueError(
                f"ZIP prefix {prefix!r} has length {len(prefix)}, "
                f"expected {prefix_length}."
            )

        if prefix in prefixes:
            raise ValueError(
                f"Duplicate {prefix_length}-digit ZIP prefix "
                f"{prefix!r}."
            )

        prefixes.add(prefix)

    return sorted(prefixes)


def create_display(
    prefix: str,
) -> str:
    """Convert a ZIP prefix to its five-position display representation."""
    return (
        prefix
        + "-" * (5 - len(prefix))
    )


def render_question_array(
    prefix_length: int,
    prefixes: list[str],
) -> str:
    """Render one generated TypeScript ZIP-prefix question array."""
    constant_name = CONSTANT_NAMES[
        prefix_length
    ]

    lines = [
        (
            f"export const {constant_name}: "
            'FeatureQuiz["questions"] = ['
        ),
    ]

    for prefix in prefixes:
        display = create_display(
            prefix
        )

        lines.append(
            f'  {{ answer: "{prefix}", '
            f'display: "{display}" }},'
        )

    lines.extend(
        [
            "];",
            "",
        ]
    )

    return "\n".join(lines)


def create_source(
    prefix_sets: dict[int, list[str]],
) -> str:
    """Create the generated TypeScript ZIP-code data module."""
    arrays = "\n".join(
        render_question_array(
            prefix_length,
            prefix_sets[prefix_length],
        )
        for prefix_length in PREFIX_LENGTHS
    )

    return f'''/**
 * Generated from the United States processed ZIP-code prefix GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/usa/generate/zip-codes-quiz-data.py
 */

import type {{ FeatureQuiz }} from "@/types/quiz";

{arrays}'''


def main() -> None:
    """Generate all United States ZIP-code prefix quiz data."""
    print(
        "Generating US ZIP-code quiz data...\n"
    )

    prefix_sets: dict[int, list[str]] = {}

    for prefix_length in PREFIX_LENGTHS:
        features = load_features(
            prefix_length
        )

        prefixes = collect_prefixes(
            features,
            prefix_length,
        )

        prefix_sets[
            prefix_length
        ] = prefixes

        print(
            f"{prefix_length}-digit prefixes: "
            f"{len(prefixes):,}"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            prefix_sets
        ),
        encoding="utf-8",
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()