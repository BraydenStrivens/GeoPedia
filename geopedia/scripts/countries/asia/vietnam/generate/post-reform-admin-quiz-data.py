"""
Generate Vietnam post-reform administrative quiz question data.

This script reads GeoPedia's finalized, simplified post-reform Vietnam
administrative GeoJSON files and generates TypeScript question arrays for:

    - 34 provinces / centrally governed cities
    - 3,321 commune-level units

The post-reform data uses Vietnam's two-tier administrative structure, so
commune-level units belong directly to provinces rather than districts.

Duplicate display-name handling:
    - Province names are already globally unique.
    - Duplicated commune-level names receive their province as a parent label:
          Tân An (Province Name)
    - The current finalized dataset becomes fully unique after this
      immediate-parent normalization.

Inputs:
    public/data/countries/vietnam/geojson/
        post-reform-provinces.geojson
        post-reform-communes.geojson

Output:
    src/quiz/quizzes/countries/asia/vietnam/data/
        post-reform-admin.ts

Run from the GeoPedia project root:

    python scripts/countries/asia/vietnam/generate/post-reform-admin-quiz-data.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


GEOJSON_DIR = Path(
    "public/data/countries/vietnam/geojson"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/asia/vietnam/data/"
    "post-reform-admin.ts"
)

PROVINCES_PATH = GEOJSON_DIR / "post-reform-provinces.geojson"
COMMUNES_PATH = GEOJSON_DIR / "post-reform-communes.geojson"

EXPECTED_PROVINCES = 34
EXPECTED_COMMUNES = 3_321


def load_features(path: Path) -> list[dict[str, Any]]:
    """Load and return a GeoJSON FeatureCollection's features."""
    if not path.exists():
        raise FileNotFoundError(f"Missing input: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return features


def validate_features(
    features: list[dict[str, Any]],
    *,
    name: str,
    id_property: str,
    name_property: str,
    expected_count: int,
) -> None:
    """Validate IDs and names required for quiz generation."""
    if len(features) != expected_count:
        raise ValueError(
            f"{name}: expected {expected_count:,} features, "
            f"found {len(features):,}."
        )

    ids: list[str] = []

    for feature in features:
        properties = feature.get("properties", {})

        feature_id = str(
            properties.get(id_property, "")
        ).strip()

        feature_name = str(
            properties.get(name_property, "")
        ).strip()

        if not feature_id:
            raise ValueError(
                f"{name}: feature has blank {id_property}."
            )

        if not feature_name:
            raise ValueError(
                f"{name}: feature {feature_id!r} has blank "
                f"{name_property}."
            )

        ids.append(feature_id)

    duplicate_ids = [
        feature_id
        for feature_id, count in Counter(ids).items()
        if count > 1
    ]

    if duplicate_ids:
        raise ValueError(
            f"{name}: duplicate {id_property} values found: "
            f"{duplicate_ids[:10]}"
        )


def duplicate_names(
    features: list[dict[str, Any]],
    *,
    name_property: str,
) -> set[str]:
    """Return raw names that occur more than once globally."""
    names = [
        str(
            feature["properties"][name_property]
        ).strip()
        for feature in features
    ]

    counts = Counter(names)

    return {
        name
        for name, count in counts.items()
        if count > 1
    }


def make_questions(
    features: list[dict[str, Any]],
    *,
    id_property: str,
    name_property: str,
    parent_name_property: str | None = None,
) -> tuple[list[dict[str, str]], int, int]:
    """
    Build quiz questions and normalize duplicated names with their parent.

    Returns:
        questions
        number of features whose labels were parent-normalized
        number of duplicate display-label groups remaining afterward
    """
    duplicates = duplicate_names(
        features,
        name_property=name_property,
    )

    questions: list[dict[str, str]] = []
    normalized_count = 0

    for feature in features:
        properties = feature["properties"]

        answer = str(
            properties[id_property]
        ).strip()

        name = str(
            properties[name_property]
        ).strip()

        display = name

        if name in duplicates and parent_name_property:
            parent_name = str(
                properties.get(parent_name_property, "")
            ).strip()

            if not parent_name:
                raise ValueError(
                    f"{answer}: duplicated {name_property} "
                    f"{name!r} has no {parent_name_property}."
                )

            display = f"{name} ({parent_name})"
            normalized_count += 1

        questions.append(
            {
                "answer": answer,
                "display": display,
            }
        )

    display_counts = Counter(
        question["display"]
        for question in questions
    )

    remaining_duplicate_groups = sum(
        1
        for count in display_counts.values()
        if count > 1
    )

    return (
        questions,
        normalized_count,
        remaining_duplicate_groups,
    )


def ts_string(value: str) -> str:
    """Encode a Python string as a TypeScript-compatible JSON string."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_question_array(
    export_name: str,
    questions: list[dict[str, str]],
) -> str:
    """Render one FeatureQuizQuestion[] TypeScript export."""
    lines = [
        (
            f"export const {export_name}: "
            "FeatureQuizQuestion[] = ["
        )
    ]

    for question in questions:
        lines.append(
            "  { "
            f"answer: {ts_string(question['answer'])}, "
            f"display: {ts_string(question['display'])} "
            "},"
        )

    lines.append("];")

    return "\n".join(lines)


def main() -> None:
    """Generate all post-reform administrative quiz data."""
    print(
        "Generating Vietnam post-reform administrative quiz data..."
    )

    provinces = load_features(PROVINCES_PATH)
    communes = load_features(COMMUNES_PATH)

    validate_features(
        provinces,
        name="Provinces",
        id_property="province_id",
        name_property="province",
        expected_count=EXPECTED_PROVINCES,
    )

    validate_features(
        communes,
        name="Commune-level units",
        id_property="commune_id",
        name_property="commune",
        expected_count=EXPECTED_COMMUNES,
    )

    (
        province_questions,
        province_normalized,
        province_remaining,
    ) = make_questions(
        provinces,
        id_property="province_id",
        name_property="province",
    )

    (
        commune_questions,
        commune_normalized,
        commune_remaining,
    ) = make_questions(
        communes,
        id_property="commune_id",
        name_property="commune",
        parent_name_property="province",
    )

    sections = [
        """/**
 * Vietnam post-reform administrative quiz question data.
 *
 * Generated from GeoPedia's finalized post-reform administrative GeoJSON.
 * Commune-level units belong directly to provinces in the two-tier
 * administrative structure represented by this dataset.
 *
 * Duplicate commune-level names are disambiguated with their province.
 * Stable feature IDs remain the quiz answers.
 *
 * Regenerate with:
 *   python scripts/countries/asia/vietnam/generate/post-reform-admin-quiz-data.py
 */

import type { FeatureQuizQuestion } from "@/types/quiz";
""",
        render_question_array(
            "VIETNAM_POST_REFORM_PROVINCE_QUESTIONS",
            province_questions,
        ),
        render_question_array(
            "VIETNAM_POST_REFORM_COMMUNE_QUESTIONS",
            commune_questions,
        ),
    ]

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        "\n\n".join(sections) + "\n",
        encoding="utf-8",
    )

    print()
    print("Vietnam post-reform quiz-data generation complete.")
    print(
        f"Provinces: {len(province_questions):,} "
        f"({province_normalized:,} parent-normalized, "
        f"{province_remaining:,} duplicate label groups remain)"
    )
    print(
        f"Communes:  {len(commune_questions):,} "
        f"({commune_normalized:,} parent-normalized, "
        f"{commune_remaining:,} duplicate label groups remain)"
    )
    print()
    print(f"Wrote: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()