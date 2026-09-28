"""
Generate Philippines administrative quiz-question data for GeoPedia.

This script reads GeoPedia's finalized public Philippines administrative
GeoJSON files and generates TypeScript question arrays used by the feature
quizzes.

Public GeoJSON inputs
---------------------
    public/data/countries/philippines/geojson/
        regions.geojson
        provinces.geojson
        municipalities-cities.geojson
        barangays.geojson

Generated TypeScript outputs
----------------------------
    src/quiz/quizzes/countries/asia/philippines/data/
        admin.ts
        municipalities-cities.ts
        barangays.ts

Output organization
-------------------
admin.ts:
    - 17 region questions
    - 88 province / province-level-unit questions

municipalities-cities.ts:
    - 1,642 municipality / city questions

barangays.ts:
    - 42,048 barangay questions

Question answers
----------------
Each question uses the stable administrative pcode as its `answer`.

For example:

    {
      answer: "PH01028",
      display: "Ilocos Norte",
    }

The corresponding map config can therefore use the stable ID property as its
answer property.

Duplicate-name disambiguation
-----------------------------
Region and Admin 2 names are globally unique, so their display labels contain
only their names.

Admin 3 contains names that repeat across different Admin 2 parents. When an
Admin 3 name is globally duplicated, its immediate Admin 2 parent is appended:

    San Isidro (Province Name)

Admin 4 contains many globally duplicated barangay names. When a barangay name
is duplicated, its immediate Admin 3 parent is appended:

    Poblacion (Municipality / City Name)

The source datasets were previously inspected and confirmed to contain no
duplicate Admin 3 names within the same immediate Admin 2 parent and no
duplicate Admin 4 names within the same immediate Admin 3 parent. Therefore,
one immediate parent is sufficient to disambiguate every generated question.

Generation rules
----------------
- Questions are sorted alphabetically by display label.
- Stable pcodes are preserved exactly.
- Every answer must be unique.
- Every display label must be unique after disambiguation.
- The expected feature/question counts are validated.
- Existing output files are replaced.

Regeneration
------------
First regenerate/process/simplify the Philippines administrative GeoJSON if
necessary, then run from the GeoPedia project root:

    python scripts/countries/philippines/generate/admin-quiz-data.py

No third-party Python packages are required.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

PUBLIC_GEOJSON_DIRECTORY = (
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


# ---------------------------------------------------------------------------
# Dataset definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuizDataset:
    """Configuration for one generated administrative question set."""

    label: str
    filename: str
    expected_count: int

    id_property: str
    name_property: str

    parent_name_property: str | None
    
    allow_duplicate_displays: bool = False


DATASETS = {
    "regions": QuizDataset(
        label="Regions",
        filename="regions.geojson",
        expected_count=17,
        id_property="region_id",
        name_property="region",
        parent_name_property=None,
    ),
    "provinces": QuizDataset(
        label="Provinces / Province-Level Units",
        filename="provinces.geojson",
        expected_count=84,
        id_property="province_id",
        name_property="province",
        parent_name_property=None,
    ),
    "municipalities_cities": QuizDataset(
        label="Municipalities / Cities",
        filename="municipalities-cities.geojson",
        expected_count=1_642,
        id_property="municipality_city_id",
        name_property="municipality_city",
        parent_name_property="province",
    ),
    "barangays": QuizDataset(
        label="Barangays",
        filename="barangays.geojson",
        expected_count=42_048,
        id_property="barangay_id",
        name_property="barangay",
        parent_name_property="municipality_city",
        allow_duplicate_displays=True,
    ),
}


# ---------------------------------------------------------------------------
# Question representation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Question:
    """One generated GeoPedia feature-quiz question."""

    answer: str
    display: str


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def require_non_empty_string(
    value: Any,
    *,
    dataset: QuizDataset,
    property_name: str,
    feature_number: int,
) -> str:
    """Validate and return a required non-empty string."""

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{dataset.label}: feature {feature_number:,} has a non-string "
            f"{property_name!r} value."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{dataset.label}: feature {feature_number:,} has a blank "
            f"{property_name!r} value."
        )

    return value


# ---------------------------------------------------------------------------
# GeoJSON loading
# ---------------------------------------------------------------------------


def load_features(
    dataset: QuizDataset,
) -> list[dict[str, Any]]:
    """Load and validate the feature array for one public dataset."""

    path = (
        PUBLIC_GEOJSON_DIRECTORY
        / dataset.filename
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Public GeoJSON not found:\n{path}\n\n"
            "Run scripts/countries/philippines/process/simplify-admin.py "
            "first."
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(
            file
        )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{dataset.label}: GeoJSON root is not an object."
        )

    if data.get(
        "type"
    ) != "FeatureCollection":
        raise ValueError(
            f"{dataset.label}: expected a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{dataset.label}: GeoJSON does not contain a feature array."
        )

    if len(
        features
    ) != dataset.expected_count:
        raise ValueError(
            f"{dataset.label}: expected {dataset.expected_count:,} features "
            f"but found {len(features):,}."
        )

    return features


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def generate_questions(
    dataset: QuizDataset,
) -> list[Question]:
    """
    Generate and validate questions for one administrative level.

    Globally duplicated names are disambiguated by appending the feature's
    immediate parent name when the dataset defines a parent_name_property.
    """

    features = load_features(
        dataset
    )

    records: list[
        tuple[
            str,
            str,
            str | None,
        ]
    ] = []

    seen_answers: set[str] = set()

    for feature_number, feature in enumerate(
        features,
        start=1,
    ):
        if not isinstance(
            feature,
            dict,
        ):
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} is not an "
                "object."
            )

        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} does not "
                "contain a properties object."
            )

        answer = require_non_empty_string(
            properties.get(
                dataset.id_property
            ),
            dataset=dataset,
            property_name=dataset.id_property,
            feature_number=feature_number,
        )

        name = require_non_empty_string(
            properties.get(
                dataset.name_property
            ),
            dataset=dataset,
            property_name=dataset.name_property,
            feature_number=feature_number,
        )

        if answer in seen_answers:
            raise ValueError(
                f"{dataset.label}: duplicate answer ID {answer!r}."
            )

        seen_answers.add(
            answer
        )

        parent_name: str | None = None

        if dataset.parent_name_property is not None:
            parent_name = require_non_empty_string(
                properties.get(
                    dataset.parent_name_property
                ),
                dataset=dataset,
                property_name=dataset.parent_name_property,
                feature_number=feature_number,
            )

        records.append(
            (
                answer,
                name,
                parent_name,
            )
        )

    name_counts = Counter(
        name
        for _, name, _ in records
    )

    questions: list[Question] = []

    for answer, name, parent_name in records:
        display = name

        if name_counts[
            name
        ] > 1:
            if parent_name is None:
                raise ValueError(
                    f"{dataset.label}: duplicate name {name!r} cannot be "
                    "disambiguated because this dataset has no configured "
                    "parent property."
                )

            display = (
                f"{name} ({parent_name})"
            )

        questions.append(
            Question(
                answer=answer,
                display=display,
            )
        )

    display_counts = Counter(
        question.display
        for question in questions
    )

    duplicate_displays = sorted(
        display
        for display, count in display_counts.items()
        if count > 1
    )

    if duplicate_displays and not dataset.allow_duplicate_displays:
        preview = ", ".join(
            repr(
                value
            )
            for value in duplicate_displays[
                :10
            ]
        )

        raise ValueError(
            f"{dataset.label}: display labels are still duplicated after "
            f"parent disambiguation. Examples: {preview}"
        )

    if len(
        questions
    ) != dataset.expected_count:
        raise ValueError(
            f"{dataset.label}: expected {dataset.expected_count:,} generated "
            f"questions but created {len(questions):,}."
        )

    questions.sort(
        key=lambda question: (
            question.display.casefold(),
            question.answer,
        )
    )

    return questions


# ---------------------------------------------------------------------------
# TypeScript formatting
# ---------------------------------------------------------------------------


def typescript_string(
    value: str,
) -> str:
    """Encode a Python string as a TypeScript-compatible JSON string."""

    return json.dumps(
        value,
        ensure_ascii=False,
    )


def format_question_array(
    export_name: str,
    questions: list[Question],
) -> str:
    """Format one generated question array as a typed TypeScript array."""

    lines = [
        f"export const {export_name}: FeatureQuizQuestion[] = [",
    ]

    for question in questions:
        lines.extend(
            [
                "  {",
                f"    answer: {typescript_string(question.answer)},",
                f"    display: {typescript_string(question.display)},",
                "  },",
            ]
        )

    lines.append(
        "];"
    )

    return "\n".join(
        lines
    )


# ---------------------------------------------------------------------------
# TypeScript files
# ---------------------------------------------------------------------------


def write_admin_file(
    region_questions: list[Question],
    province_questions: list[Question],
) -> Path:
    """Write Admin 1 and Admin 2 question arrays."""

    path = (
        OUTPUT_DIRECTORY
        / "admin.ts"
    )

    content = f"""/**
 * Generated Philippines Admin 1 and Admin 2 quiz-question data.
 *
 * DO NOT EDIT THIS FILE MANUALLY.
 *
 * Generated by:
 *   scripts/countries/philippines/generate/admin-quiz-data.py
 *
 * Source GeoJSON:
 *   public/data/countries/philippines/geojson/regions.geojson
 *   public/data/countries/philippines/geojson/provinces.geojson
 *
 * The stable administrative pcode is used as `answer`, while `display`
 * contains the player-facing administrative name.
 */
 
import {{ FeatureQuizQuestion }} from "@/types/quiz";

{format_question_array("PHILIPPINES_REGION_QUESTIONS", region_questions)}

{format_question_array("PHILIPPINES_PROVINCE_QUESTIONS", province_questions)}
"""

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def write_municipalities_cities_file(
    questions: list[Question],
) -> Path:
    """Write Admin 3 municipality/city question data."""

    path = (
        OUTPUT_DIRECTORY
        / "municipalities-cities.ts"
    )

    content = f"""/**
 * Generated Philippines municipality / city quiz-question data.
 *
 * DO NOT EDIT THIS FILE MANUALLY.
 *
 * Generated by:
 *   scripts/countries/philippines/generate/admin-quiz-data.py
 *
 * Source GeoJSON:
 *   public/data/countries/philippines/geojson/municipalities-cities.geojson
 *
 * The stable Admin 3 pcode is used as `answer`.
 *
 * Globally duplicated municipality/city names are disambiguated by appending
 * their immediate Admin 2 parent. Unique names are left unchanged.
 */
 
import {{ FeatureQuizQuestion }} from "@/types/quiz";

{format_question_array(
    "PHILIPPINES_MUNICIPALITY_CITY_QUESTIONS",
    questions,
)}
"""

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def write_barangays_file(
    questions: list[Question],
) -> Path:
    """Write Admin 4 barangay question data."""

    path = (
        OUTPUT_DIRECTORY
        / "barangays.ts"
    )

    content = f"""/**
 * Generated Philippines barangay quiz-question data.
 *
 * DO NOT EDIT THIS FILE MANUALLY.
 *
 * Generated by:
 *   scripts/countries/philippines/generate/admin-quiz-data.py
 *
 * Source GeoJSON:
 *   public/data/countries/philippines/geojson/barangays.geojson
 *
 * The stable Admin 4 pcode is used as `answer`.
 *
 * Globally duplicated barangay names are disambiguated by appending their
 * immediate municipality/city parent. Unique names are left unchanged.
 */
 
import {{ FeatureQuizQuestion }} from "@/types/quiz";

{format_question_array("PHILIPPINES_BARANGAY_QUESTIONS", questions)}
"""

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def duplicate_name_count(
    dataset: QuizDataset,
) -> tuple[int, int]:
    """
    Return:
        - number of distinct names that are duplicated
        - number of features whose names require disambiguation
    """

    features = load_features(
        dataset
    )

    names: list[str] = []

    for feature_number, feature in enumerate(
        features,
        start=1,
    ):
        properties = feature.get(
            "properties"
        )

        if not isinstance(
            properties,
            dict,
        ):
            raise ValueError(
                f"{dataset.label}: feature {feature_number:,} has invalid "
                "properties."
            )

        names.append(
            require_non_empty_string(
                properties.get(
                    dataset.name_property
                ),
                dataset=dataset,
                property_name=dataset.name_property,
                feature_number=feature_number,
            )
        )

    counts = Counter(
        names
    )

    duplicated_names = sum(
        1
        for count in counts.values()
        if count > 1
    )

    affected_features = sum(
        count
        for count in counts.values()
        if count > 1
    )

    return (
        duplicated_names,
        affected_features,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(
        "Generating Philippines administrative quiz data..."
    )
    print()

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    regions = generate_questions(
        DATASETS[
            "regions"
        ]
    )

    print(
        f"Regions: {len(regions):,} questions"
    )

    provinces = generate_questions(
        DATASETS[
            "provinces"
        ]
    )

    print(
        f"Provinces / Province-Level Units: {len(provinces):,} questions"
    )

    municipalities_cities = generate_questions(
        DATASETS[
            "municipalities_cities"
        ]
    )

    admin3_duplicate_names, admin3_affected = duplicate_name_count(
        DATASETS[
            "municipalities_cities"
        ]
    )

    print(
        f"Municipalities / Cities: {len(municipalities_cities):,} questions"
    )
    print(
        f"  Duplicate names: {admin3_duplicate_names:,}"
    )
    print(
        f"  Parent-qualified displays: {admin3_affected:,}"
    )

    barangays = generate_questions(
        DATASETS[
            "barangays"
        ]
    )

    admin4_duplicate_names, admin4_affected = duplicate_name_count(
        DATASETS[
            "barangays"
        ]
    )

    print(
        f"Barangays: {len(barangays):,} questions"
    )
    print(
        f"  Duplicate names: {admin4_duplicate_names:,}"
    )
    print(
        f"  Parent-qualified displays: {admin4_affected:,}"
    )

    print()

    admin_path = write_admin_file(
        regions,
        provinces,
    )

    municipalities_cities_path = write_municipalities_cities_file(
        municipalities_cities
    )

    barangays_path = write_barangays_file(
        barangays
    )

    print(
        "Generated:"
    )

    for path in (
        admin_path,
        municipalities_cities_path,
        barangays_path,
    ):
        size_kb = (
            path.stat().st_size
            / 1024
        )

        print(
            f"  {path.relative_to(PROJECT_ROOT)}"
        )
        print(
            f"    {size_kb:,.1f} KB"
        )

    print()
    print(
        "=" * 78
    )
    print(
        "Philippines administrative quiz-data generation complete."
    )
    print(
        "=" * 78
    )


if __name__ == "__main__":
    main()