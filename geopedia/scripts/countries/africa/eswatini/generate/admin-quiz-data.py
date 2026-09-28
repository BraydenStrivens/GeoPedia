"""
Generate Eswatini administrative quiz question data for GeoPedia.

Inputs:

    public/data/countries/eswatini/geojson/
        regions.geojson
        tinkhundla.geojson

Output:

    src/quiz/quizzes/countries/africa/eswatini/data/admin.ts

Generated arrays:

    ESWATINI_REGION_QUIZ_QUESTIONS
    ESWATINI_TINKHUNDLA_QUIZ_QUESTIONS

Each question uses the canonical GeoJSON feature ID as its answer and the
human-readable administrative name as its display value.

Run from the GeoPedia project root:

    python scripts/countries/eswatini/generate/admin-quiz-data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


INPUT_DIR = Path(
    "public/data/countries/eswatini/geojson"
)

REGIONS_INPUT = (
    INPUT_DIR
    / "regions.geojson"
)

TINKHUNDLA_INPUT = (
    INPUT_DIR
    / "tinkhundla.geojson"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/countries/africa/eswatini/data/admin.ts"
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
    display_property: str,
) -> list[tuple[str, str]]:
    """
    Extract and validate quiz questions.

    Each tuple contains:

        (answer, display)

    The answer is the GeoJSON feature ID used by the quiz runtime to identify
    the correct map feature. The display value is the human-readable name
    shown to the user.
    """
    data = load_geojson(
        path
    )

    questions: list[
        tuple[str, str]
    ] = []

    seen_answers: set[str] = set()

    for index, feature in enumerate(
        data["features"]
    ):
        properties = feature.get(
            "properties",
            {},
        )

        answer = properties.get(
            id_property
        )

        display = properties.get(
            display_property
        )

        if not isinstance(
            answer,
            str,
        ) or not answer:
            raise ValueError(
                f"{path}: feature {index} is missing "
                f"a valid {id_property}."
            )

        if not isinstance(
            display,
            str,
        ) or not display:
            raise ValueError(
                f"{path}: feature {answer} is missing "
                f"a valid {display_property}."
            )

        if answer in seen_answers:
            raise ValueError(
                f"{path}: duplicate answer {answer!r}."
            )

        seen_answers.add(
            answer
        )

        questions.append(
            (
                answer,
                display,
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
    """Encode a string as a TypeScript-compatible JSON string."""
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

    for answer, display in questions:
        if answer == display:
            lines.append(
                "  { "
                f"answer: {ts_string(answer)} "
                "},"
            )
        else:
            lines.append(
                "  { "
                f"answer: {ts_string(answer)}, "
                f"display: {ts_string(display)} "
                "},"
            )

    lines.append(
        "];"
    )

    return "\n".join(
        lines
    )


def main() -> None:
    """Generate Eswatini region and tinkhundla quiz data."""
    print(
        "Generating Eswatini administrative quiz data..."
    )

    region_questions = collect_questions(
        REGIONS_INPUT,
        "region_id",
        "region",
    )

    tinkhundla_questions = collect_questions(
        TINKHUNDLA_INPUT,
        "inkhundla_id",
        "inkhundla",
    )

    print(
        f"Region questions: "
        f"{len(region_questions):,}"
    )

    print(
        f"Tinkhundla questions: "
        f"{len(tinkhundla_questions):,}"
    )

    output = (
        "/**\n"
        " * Generated Eswatini administrative quiz question data.\n"
        " *\n"
        " * Do not edit this file manually.\n"
        " *\n"
        " * Regenerate with:\n"
        " *   python scripts/countries/eswatini/generate/admin-quiz-data.py\n"
        " */\n\n"
        'import type { FeatureQuizQuestion } from "@/types/quiz";\n\n'
        + render_question_array(
            "ESWATINI_REGION_QUIZ_QUESTIONS",
            region_questions,
        )
        + "\n\n"
        + render_question_array(
            "ESWATINI_TINKHUNDLA_QUIZ_QUESTIONS",
            tinkhundla_questions,
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