"""
Generate Malaysia administrative quiz question data for GeoPedia.

This script reads GeoPedia's finalized public Malaysian administrative
GeoJSON files and generates the TypeScript question arrays used by the
country's three administrative quizzes:

- Negeri & Wilayah Persekutuan (States & Federal Territories)
- Daerah (Districts)
- Mukim (Sub-Districts)

The processed GeoJSON already contains GeoPedia's canonical stable IDs,
display names, and parent hierarchy. Source administrative names are
preserved exactly, including ADM3 terms such as MUKIM, PEKAN, BANDAR,
LAND DISTRICT, and TOWN DISTRICT.

Questions use the stable feature ID as `answer` and the administrative name
as `display`.

Inputs
------
public/data/countries/malaysia/geojson/states.geojson
public/data/countries/malaysia/geojson/districts.geojson
public/data/countries/malaysia/geojson/sub-districts.geojson

Output
------
src/quiz/quizzes/countries/asia/malaysia/data/admin.ts

Run from the GeoPedia project root:

    python scripts/countries/asia/malaysia/generate/admin.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[5]

GEOJSON_DIR = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "malaysia"
    / "geojson"
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
    / "admin.ts"
)

STATES_PATH = GEOJSON_DIR / "states.geojson"
DISTRICTS_PATH = GEOJSON_DIR / "districts.geojson"
SUB_DISTRICTS_PATH = GEOJSON_DIR / "sub-districts.geojson"


# ---------------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------------

DATASETS = (
    {
        "label": "States & Federal Territories",
        "path": STATES_PATH,
        "constant": "MALAYSIA_STATE_QUESTIONS",
        "id_property": "state_id",
        "name_property": "state",
        "expected_count": 16,
        "normalize_display": False,
    },
    {
        "label": "Districts",
        "path": DISTRICTS_PATH,
        "constant": "MALAYSIA_DISTRICT_QUESTIONS",
        "id_property": "district_id",
        "name_property": "district",
        "expected_count": 159,
        "normalize_display": False,
    },
    {
        "label": "Sub-Districts",
        "path": SUB_DISTRICTS_PATH,
        "constant": "MALAYSIA_SUB_DISTRICT_QUESTIONS",
        "id_property": "sub_district_id",
        "name_property": "sub_district",
        "expected_count": 1859,
        "normalize_display": True,
    },
)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_features(
    path: Path,
) -> list[dict[str, Any]]:
    """Load the feature array from one processed GeoJSON file."""

    if not path.exists():
        raise FileNotFoundError(
            f"Missing processed GeoJSON: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        geojson = json.load(file)

    features = geojson.get(
        "features"
    )

    if not isinstance(features, list):
        raise ValueError(
            f"{path.name} does not contain a valid GeoJSON feature array."
        )

    return features


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def normalize_sub_district_name(
    value: str,
) -> str:
    """
    Normalize an ADM3 name for player-facing quiz labels.

    Malaysia's ADM3 source data is almost entirely uppercase. Preserve the
    complete administrative name while converting each word to title case.
    """

    return value.title()

def build_questions(
    features: list[dict[str, Any]],
    id_property: str,
    name_property: str,
    expected_count: int,
    label: str,
    normalize_display: bool = False,
) -> list[dict[str, str]]:
    """
    Build and validate one administrative question set.

    Questions are sorted alphabetically by their display name so generated
    output remains deterministic and easy to inspect.
    """

    if len(features) != expected_count:
        raise ValueError(
            f"{label} expected {expected_count:,} features but found "
            f"{len(features):,}."
        )

    questions: list[dict[str, str]] = []

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        answer = properties.get(
            id_property
        )

        display = properties.get(
            name_property
        )

        if answer is None or str(answer).strip() == "":
            raise ValueError(
                f"{label} contains a feature without {id_property}."
            )

        if display is None or str(display).strip() == "":
            raise ValueError(
                f"{label} contains a feature without {name_property}."
            )

        display = str(display).strip()

        if normalize_display:
            display = normalize_sub_district_name(
                display
            )

        questions.append(
            {
                "answer": str(answer),
                "display": display,
            }
        )

    answers = [
        question["answer"]
        for question in questions
    ]

    displays = [
        question["display"]
        for question in questions
    ]

    if len(answers) != len(set(answers)):
        raise ValueError(
            f"{label} contains duplicate question answers."
        )

    if len(displays) != len(set(displays)):
        raise ValueError(
            f"{label} contains duplicate question display names."
        )

    questions.sort(
        key=lambda question: question["display"].casefold()
    )

    return questions


# ---------------------------------------------------------------------------
# TypeScript generation
# ---------------------------------------------------------------------------


def typescript_string(
    value: str,
) -> str:
    """Encode a Python string as a valid JSON/TypeScript string literal."""

    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_question_array(
    constant_name: str,
    questions: list[dict[str, str]],
) -> str:
    """Render one FeatureQuizQuestion TypeScript array."""

    lines = [
        (
            f"export const {constant_name}: "
            "FeatureQuizQuestion[] = ["
        )
    ]

    for question in questions:
        answer = typescript_string(
            question["answer"]
        )

        display = typescript_string(
            question["display"]
        )

        lines.append(
            f"  {{ answer: {answer}, display: {display} }},"
        )

    lines.append("];")

    return "\n".join(lines)


def generate_typescript() -> tuple[str, list[tuple[str, int]]]:
    """Generate the complete Malaysia administrative question-data module."""

    sections: list[str] = []
    counts: list[tuple[str, int]] = []

    for dataset in DATASETS:
        features = load_features(
            dataset["path"]
        )

        questions = build_questions(
            features=features,
            id_property=dataset["id_property"],
            name_property=dataset["name_property"],
            expected_count=dataset["expected_count"],
            label=dataset["label"],
            normalize_display=dataset["normalize_display"],
        )

        sections.append(
            render_question_array(
                dataset["constant"],
                questions,
            )
        )

        counts.append(
            (
                dataset["label"],
                len(questions),
            )
        )

    header = """/**
/**
 * Malaysia administrative quiz question data.
 *
 * Generated from GeoPedia's processed public administrative GeoJSON.
 *
 * Contains question sets for:
 * - States & Federal Territories
 * - Districts
 * - Sub-Districts
 *
 * ADM3 labels preserve their complete administrative names while normalizing
 * the source's uppercase formatting to title case.
 *
 * Regenerate with:
 * python scripts/countries/asia/malaysia/generate/admin-quiz-data.py
 */

import { FeatureQuizQuestion } from "@/types/quiz";
"""

    content = (
        header
        + "\n\n"
        + "\n\n".join(sections)
        + "\n"
    )

    return content, counts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Generate Malaysia administrative quiz question data."""

    print()
    print(
        "Generating Malaysia administrative quiz data..."
    )
    print()

    content, counts = generate_typescript()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )

    for label, count in counts:
        print(
            f"  {label}: {count:,} questions"
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
        "Malaysia administrative quiz-data generation complete."
    )


if __name__ == "__main__":
    main()