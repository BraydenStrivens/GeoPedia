"""
Generate Lesotho administrative quiz question data for GeoPedia.

Inputs:

    data/intermediate/countries/lesotho/admin/
        districts.geojson
        constituencies.geojson

Output:

    src/quiz/quizzes/countries/africa/lesotho/data/admin.ts

Generated arrays:

    LESOTHO_DISTRICT_QUIZ_QUESTIONS
    LESOTHO_CONSTITUENCY_QUIZ_QUESTIONS

Each question uses the canonical feature ID as its stable ID and the
canonical administrative name as its answer.

Constituency names are unique, so no district-qualified display values are
required.

Run from the GeoPedia project root:

    python scripts/countries/lesotho/generate/admin-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


INPUT_DIR = Path(
    "data/intermediate/countries/lesotho/admin"
)

DISTRICTS_INPUT = (
    INPUT_DIR
    / "districts.geojson"
)

CONSTITUENCIES_INPUT = (
    INPUT_DIR
    / "constituencies.geojson"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/africa/lesotho/data/admin.ts"
)


def load_geojson(
    path: Path,
) -> dict[str, Any]:
    """Load and validate a GeoJSON FeatureCollection."""
    if not path.exists():
        raise FileNotFoundError(
            f"GeoJSON file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if (
        data.get("type")
        != "FeatureCollection"
    ):
        raise ValueError(
            f"{path} is not a GeoJSON FeatureCollection."
        )

    features = data.get(
        "features"
    )

    if not isinstance(
        features,
        list,
    ):
        raise ValueError(
            f"{path} does not contain a valid features array."
        )

    return data


def collect_questions(
    path: Path,
    id_property: str,
    answer_property: str,
) -> list[tuple[str, str]]:
    """
    Extract and validate quiz questions from one canonical GeoJSON dataset.

    Returns tuples of:

        (feature_id, answer)
    """
    data = load_geojson(
        path
    )

    questions: list[
        tuple[str, str]
    ] = []

    seen_ids: set[str] = set()
    seen_answers: set[str] = set()

    for index, feature in enumerate(
        data["features"]
    ):
        properties = feature.get(
            "properties",
            {},
        )

        feature_id = properties.get(
            id_property
        )

        answer = properties.get(
            answer_property
        )

        if not isinstance(
            feature_id,
            str,
        ) or not feature_id:
            raise ValueError(
                f"{path}: feature {index} is missing "
                f"a valid {id_property}."
            )

        if not isinstance(
            answer,
            str,
        ) or not answer:
            raise ValueError(
                f"{path}: feature {feature_id} is missing "
                f"a valid {answer_property}."
            )

        if feature_id in seen_ids:
            raise ValueError(
                f"{path}: duplicate feature ID "
                f"{feature_id!r}."
            )

        if answer in seen_answers:
            raise ValueError(
                f"{path}: duplicate quiz answer "
                f"{answer!r}."
            )

        seen_ids.add(
            feature_id
        )

        seen_answers.add(
            answer
        )

        questions.append(
            (
                feature_id,
                answer,
            )
        )

    questions.sort(
        key=lambda question: (
            question[1].casefold(),
            question[0],
        )
    )

    return questions


def ts_string(
    value: str,
) -> str:
    """Encode a Python string as a TypeScript-compatible JSON string."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def render_question_array(
    constant_name: str,
    questions: list[
        tuple[str, str]
    ],
) -> str:
    """Render one FeatureQuizQuestion array."""
    lines = [
        (
            f"export const {constant_name}: "
            "FeatureQuizQuestion[] = ["
        )
    ]

    for feature_id, answer in questions:
        lines.append(
            "  { "
            f"answer: {ts_string(feature_id)}, "
            f"display: {ts_string(answer)} "
            "},"
        )

    lines.append(
        "];"
    )

    return "\n".join(
        lines
    )


def main() -> None:
    """Generate Lesotho district and constituency quiz question data."""
    print(
        "Generating Lesotho administrative quiz data..."
    )

    district_questions = collect_questions(
        DISTRICTS_INPUT,
        "district_id",
        "district",
    )

    constituency_questions = collect_questions(
        CONSTITUENCIES_INPUT,
        "constituency_id",
        "constituency",
    )

    print(
        f"District questions: "
        f"{len(district_questions):,}"
    )

    print(
        f"Constituency questions: "
        f"{len(constituency_questions):,}"
    )

    output = (
        "/**\n"
        " * Generated Lesotho administrative quiz question data.\n"
        " *\n"
        " * Do not edit this file manually.\n"
        " *\n"
        " * Regenerate with:\n"
        " *   python scripts/countries/lesotho/generate/admin-quiz-data.py\n"
        " */\n\n"
        'import type { FeatureQuizQuestion } from "@/types/quiz";\n\n'
        + render_question_array(
            "LESOTHO_DISTRICT_QUIZ_QUESTIONS",
            district_questions,
        )
        + "\n\n"
        + render_question_array(
            "LESOTHO_CONSTITUENCY_QUIZ_QUESTIONS",
            constituency_questions,
        )
        + "\n"
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print(
        f"Wrote {OUTPUT_PATH}"
    )

    print(
        "Done."
    )


if __name__ == "__main__":
    main()