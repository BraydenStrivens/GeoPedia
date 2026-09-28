"""
Generates the question data used by GeoPedia's United States telephone
area-code quiz.

Source:
    public/data/us-area-codes.geojson

Output:
    src/quiz/quizzes/countries/north-america/usa/data/areaCodes.ts

Each distinct area code remains its own quiz question even when several
codes share the same geographic feature.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "usa"
    / "geojson"
    / "area-codes.geojson"
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
    / "areaCodes.ts"
)


def load_features() -> list[dict[str, Any]]:
    """Load and validate the processed US area-code GeoJSON."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Missing processed US area-code GeoJSON:\n"
            f"  {INPUT_PATH}"
        )

    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "US area-code GeoJSON is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "US area-code GeoJSON does not contain a feature list."
        )

    if not features:
        raise ValueError(
            "US area-code GeoJSON contains no features."
        )

    return features


def collect_area_codes(
    features: list[dict[str, Any]],
) -> list[str]:
    """Collect and validate every distinct area-code answer."""
    area_codes: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Area-code feature {index} has invalid properties."
            )

        feature_area_codes = properties.get(
            "area_codes"
        )

        if (
            not isinstance(feature_area_codes, list)
            or not feature_area_codes
        ):
            raise ValueError(
                f"Area-code feature {index} has invalid area_codes."
            )

        for area_code in feature_area_codes:
            area_code = str(area_code)

            if not area_code.isdigit():
                raise ValueError(
                    f"Invalid area code {area_code!r}."
                )

            if len(area_code) != 3:
                raise ValueError(
                    f"Area code {area_code!r} is not three digits."
                )

            area_codes.add(
                area_code
            )

    if not area_codes:
        raise ValueError(
            "No area-code answers were found."
        )

    return sorted(
        area_codes,
        key=int,
    )


def render_questions(
    area_codes: list[str],
) -> str:
    """Render the generated TypeScript question array."""
    lines = [
        'import type { FeatureQuiz } from "@/types/quiz";',
        "",
        (
            "export const US_AREA_CODE_QUESTIONS: "
            'FeatureQuiz["questions"] = ['
        ),
    ]

    for area_code in area_codes:
        lines.append(
            f'  {{ answer: "{area_code}" }},'
        )

    lines.extend(
        [
            "];",
            "",
        ]
    )

    return "\n".join(lines)


def create_source(
    area_codes: list[str],
) -> str:
    """Create the generated TypeScript area-code data module."""
    questions = render_questions(
        area_codes
    )

    return f'''/**
 * Generated from the United States processed telephone area-code GeoJSON.
 *
 * Do not edit manually.
 * Regenerate with:
 * python scripts/countries/usa/generate/area-codes-quiz-data.py
 */

{questions}'''


def main() -> None:
    """Generate United States telephone area-code quiz data."""
    print(
        "Generating US area-code quiz data...\n"
    )

    features = load_features()

    area_codes = collect_area_codes(
        features
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        create_source(
            area_codes
        ),
        encoding="utf-8",
    )

    multi_answer_features = sum(
        1
        for feature in features
        if len(
            feature["properties"]["area_codes"]
        ) > 1
    )

    print(
        f"Geographic features:   {len(features):,}"
    )
    print(
        f"Area-code questions:   {len(area_codes):,}"
    )
    print(
        f"Multi-answer features: {multi_answer_features:,}"
    )

    print(
        f"\nGenerated: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()