"""
Generate South Africa administrative quiz question data for GeoPedia.

The generated TypeScript contains complete FeatureQuizQuestion arrays for
South Africa's province, district, municipality, and ward quizzes.

Province, district, and municipality questions are written to admin.ts.
The much larger ward question set is written separately to wards.ts.

Questions are generated from the processed runtime GeoJSON so their answers
and display names remain synchronized with the map features.

Inputs:
    public/data/countries/south-africa/geojson/provinces.geojson
    public/data/countries/south-africa/geojson/districts.geojson
    public/data/countries/south-africa/geojson/municipalities.geojson
    public/data/countries/south-africa/geojson/wards.geojson

Outputs:
    src/quiz/quizzes/countries/africa/south-africa/data/admin.ts
    src/quiz/quizzes/countries/africa/south-africa/data/wards.ts

Run:
    python scripts/countries/south-africa/generate/admin-quiz-data.py
"""

import json
from collections import Counter
from pathlib import Path


PUBLIC_ROOT = Path(
    "public/data/countries/south-africa/geojson"
)

PROVINCES_PATH = PUBLIC_ROOT / "provinces.geojson"
DISTRICTS_PATH = PUBLIC_ROOT / "districts.geojson"
MUNICIPALITIES_PATH = PUBLIC_ROOT / "municipalities.geojson"
WARDS_PATH = PUBLIC_ROOT / "wards.geojson"

OUTPUT_ROOT = Path(
    "src/quiz/quizzes/countries/africa/south-africa/data"
)

ADMIN_OUTPUT_PATH = OUTPUT_ROOT / "admin.ts"
WARDS_OUTPUT_PATH = OUTPUT_ROOT / "wards.ts"

EXPECTED_PROVINCE_COUNT = 9
EXPECTED_DISTRICT_COUNT = 52
EXPECTED_MUNICIPALITY_COUNT = 213
EXPECTED_WARD_COUNT = 4392


def load_features(path: Path) -> list[dict]:
    """Load the feature array from a processed runtime GeoJSON file."""

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


def require_string(
    properties: dict,
    property_name: str,
    context: str,
) -> str:
    """Return a required non-empty string property."""

    value = properties.get(property_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{context}: invalid {property_name}: {value!r}"
        )

    return value.strip()


def validate_count(
    features: list[dict],
    expected_count: int,
    label: str,
) -> None:
    """Validate the expected number of runtime features."""

    if len(features) != expected_count:
        raise ValueError(
            f"Unexpected {label} count: "
            f"expected {expected_count}, "
            f"found {len(features)}."
        )


def get_duplicate_values(
    features: list[dict],
    property_name: str,
) -> set[str]:
    """Return values that occur more than once for a property."""

    values = []

    for index, feature in enumerate(features):
        properties = feature.get("properties") or {}

        value = require_string(
            properties,
            property_name,
            f"{property_name} feature {index}",
        )

        values.append(value)

    counts = Counter(values)

    return {
        value
        for value, count in counts.items()
        if count > 1
    }


def build_simple_questions(
    features: list[dict],
    id_property: str,
    name_property: str,
) -> list[dict]:
    """Build questions whose normal display name is already sufficient."""

    questions = []
    seen_answers = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties") or {}
        context = f"{name_property} feature {index}"

        answer = require_string(
            properties,
            id_property,
            context,
        )
        display = require_string(
            properties,
            name_property,
            context,
        )

        if answer in seen_answers:
            raise ValueError(
                f"Duplicate quiz answer: {answer}"
            )

        seen_answers.add(answer)

        questions.append(
            {
                "answer": answer,
                "display": display,
            }
        )

    questions.sort(
        key=lambda question: question["display"]
    )

    return questions


def build_district_questions(
    features: list[dict],
) -> list[dict]:
    """
    Build district questions.

    Duplicate district names are qualified with their province when needed.
    """

    duplicate_names = get_duplicate_values(
        features,
        "district",
    )

    questions = []
    seen_answers = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties") or {}
        context = f"District feature {index}"

        answer = require_string(
            properties,
            "district_id",
            context,
        )
        district = require_string(
            properties,
            "district",
            context,
        )
        province = require_string(
            properties,
            "province",
            context,
        )

        if answer in seen_answers:
            raise ValueError(
                f"Duplicate district answer: {answer}"
            )

        seen_answers.add(answer)

        display = district

        if district in duplicate_names:
            display = f"{district}, {province}"

        questions.append(
            {
                "answer": answer,
                "display": display,
            }
        )

    questions.sort(
        key=lambda question: question["display"]
    )

    return questions


def build_municipality_questions(
    features: list[dict],
) -> list[dict]:
    """
    Build municipality questions with progressive parent qualification.

    Duplicate municipality names first receive their district. If that still
    does not make the display unique, the province is appended as well.
    """

    duplicate_names = get_duplicate_values(
        features,
        "municipality",
    )

    base_rows = []

    for index, feature in enumerate(features):
        properties = feature.get("properties") or {}
        context = f"Municipality feature {index}"

        base_rows.append(
            {
                "answer": require_string(
                    properties,
                    "municipality_id",
                    context,
                ),
                "municipality": require_string(
                    properties,
                    "municipality",
                    context,
                ),
                "district": require_string(
                    properties,
                    "district",
                    context,
                ),
                "province": require_string(
                    properties,
                    "province",
                    context,
                ),
            }
        )

    seen_answers = set()
    provisional = []

    for row in base_rows:
        answer = row["answer"]

        if answer in seen_answers:
            raise ValueError(
                f"Duplicate municipality answer: {answer}"
            )

        seen_answers.add(answer)

        display = row["municipality"]

        if row["municipality"] in duplicate_names:
            display = (
                f'{row["municipality"]}, '
                f'{row["district"]}'
            )

        provisional.append(
            {
                **row,
                "display": display,
            }
        )

    display_counts = Counter(
        row["display"]
        for row in provisional
    )

    questions = []

    for row in provisional:
        display = row["display"]

        if display_counts[display] > 1:
            display = (
                f'{display}, {row["province"]}'
            )

        questions.append(
            {
                "answer": row["answer"],
                "display": display,
            }
        )

    questions.sort(
        key=lambda question: question["display"]
    )

    return questions


def build_ward_questions(
    features: list[dict],
) -> list[dict]:
    """
    Build ward questions from canonical ward IDs and names.

    The processor has already formatted each ward as:
        Ward XXX, Municipality

    If that display is still duplicated, the district is appended. If a
    collision remains after that, the province is appended as well.
    """

    rows = []
    seen_answers = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties") or {}
        context = f"Ward feature {index}"

        answer = require_string(
            properties,
            "ward_id",
            context,
        )
        ward = require_string(
            properties,
            "ward",
            context,
        )
        district = require_string(
            properties,
            "district",
            context,
        )
        province = require_string(
            properties,
            "province",
            context,
        )

        if answer in seen_answers:
            raise ValueError(
                f"Duplicate ward answer: {answer}"
            )

        seen_answers.add(answer)

        rows.append(
            {
                "answer": answer,
                "display": ward,
                "district": district,
                "province": province,
            }
        )

    first_counts = Counter(
        row["display"]
        for row in rows
    )

    for row in rows:
        if first_counts[row["display"]] > 1:
            row["display"] = (
                f'{row["display"]}, {row["district"]}'
            )

    second_counts = Counter(
        row["display"]
        for row in rows
    )

    for row in rows:
        if second_counts[row["display"]] > 1:
            row["display"] = (
                f'{row["display"]}, {row["province"]}'
            )

    questions = [
        {
            "answer": row["answer"],
            "display": row["display"],
        }
        for row in rows
    ]

    questions.sort(
        key=lambda question: question["display"]
    )

    return questions


def format_questions(
    name: str,
    questions: list[dict],
) -> str:
    """Format a FeatureQuizQuestion array as TypeScript."""

    lines = [
        f"export const {name}: FeatureQuizQuestion[] = ["
    ]

    for question in questions:
        answer = json.dumps(
            question["answer"],
            ensure_ascii=False,
        )
        display = json.dumps(
            question["display"],
            ensure_ascii=False,
        )

        lines.append(
            f"  {{ answer: {answer}, display: {display} }},"
        )

    lines.append("];")

    return "\n".join(lines)


def write_admin_file(
    province_questions: list[dict],
    district_questions: list[dict],
    municipality_questions: list[dict],
) -> None:
    """Write province, district, and municipality question data."""

    sections = [
        (
            "/**\n"
            " * Generated quiz question data for South Africa's provinces,\n"
            " * districts, and municipalities.\n"
            " *\n"
            " * Do not edit this file manually. Regenerate it with:\n"
            " * python scripts/countries/south-africa/generate/"
            "admin-quiz-data.py\n"
            " */"
        ),
        (
            'import type { FeatureQuizQuestion } '
            'from "@/types/quiz";'
        ),
        format_questions(
            "SOUTH_AFRICA_PROVINCES_QUIZ_QUESTIONS",
            province_questions,
        ),
        format_questions(
            "SOUTH_AFRICA_DISTRICTS_QUIZ_QUESTIONS",
            district_questions,
        ),
        format_questions(
            "SOUTH_AFRICA_MUNICIPALITIES_QUIZ_QUESTIONS",
            municipality_questions,
        ),
    ]

    ADMIN_OUTPUT_PATH.write_text(
        "\n\n".join(sections) + "\n",
        encoding="utf-8",
    )


def write_wards_file(
    ward_questions: list[dict],
) -> None:
    """Write the separate ward question dataset."""

    sections = [
        (
            "/**\n"
            " * Generated quiz question data for South Africa's wards.\n"
            " *\n"
            " * Ward displays use the municipality for context and add "
            "higher\n"
            " * administrative levels only when needed to distinguish "
            "duplicates.\n"
            " *\n"
            " * Do not edit this file manually. Regenerate it with:\n"
            " * python scripts/countries/south-africa/generate/"
            "admin-quiz-data.py\n"
            " */"
        ),
        (
            'import type { FeatureQuizQuestion } '
            'from "@/types/quiz";'
        ),
        format_questions(
            "SOUTH_AFRICA_WARDS_QUIZ_QUESTIONS",
            ward_questions,
        ),
    ]

    WARDS_OUTPUT_PATH.write_text(
        "\n\n".join(sections) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Generate South Africa's administrative quiz question datasets."""

    print("Generating South Africa administrative quiz data...")
    print()

    province_features = load_features(
        PROVINCES_PATH
    )
    district_features = load_features(
        DISTRICTS_PATH
    )
    municipality_features = load_features(
        MUNICIPALITIES_PATH
    )
    ward_features = load_features(
        WARDS_PATH
    )

    validate_count(
        province_features,
        EXPECTED_PROVINCE_COUNT,
        "province",
    )
    validate_count(
        district_features,
        EXPECTED_DISTRICT_COUNT,
        "district",
    )
    validate_count(
        municipality_features,
        EXPECTED_MUNICIPALITY_COUNT,
        "municipality",
    )
    validate_count(
        ward_features,
        EXPECTED_WARD_COUNT,
        "ward",
    )

    province_questions = build_simple_questions(
        province_features,
        "province_id",
        "province",
    )

    district_questions = build_district_questions(
        district_features
    )

    municipality_questions = build_municipality_questions(
        municipality_features
    )

    ward_questions = build_ward_questions(
        ward_features
    )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_admin_file(
        province_questions,
        district_questions,
        municipality_questions,
    )

    write_wards_file(
        ward_questions
    )

    print(
        f"Provinces       {len(province_questions):>4} questions"
    )
    print(
        f"Districts       {len(district_questions):>4} questions"
    )
    print(
        f"Municipalities  {len(municipality_questions):>4} questions"
    )
    print(
        f"Wards           {len(ward_questions):>4} questions"
    )
    print()
    print(f"Output: {ADMIN_OUTPUT_PATH}")
    print(f"Output: {WARDS_OUTPUT_PATH}")
    print()
    print("South Africa administrative quiz data generated.")


if __name__ == "__main__":
    main()