"""
Generate Cambodia administrative quiz question data for GeoPedia.

Reads the finalized Cambodia province, district, and commune GeoJSON files
and generates typed TypeScript question arrays.

Province and district questions include Khmer nativeDisplay values.
Commune questions intentionally omit nativeDisplay because the available
Khmer gazetteer does not exactly match the commune boundary dataset.

Input:
    public/data/countries/cambodia/geojson/
        provinces.geojson
        districts.geojson
        communes.geojson

Output:
    src/quiz/quizzes/countries/asia/cambodia/data/admin.ts

Usage:
    python scripts/countries/asia/cambodia/generate/admin.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]

GEOJSON_DIR = (
    PROJECT_ROOT
    / "public/data/countries/cambodia/geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src/quiz/quizzes/countries/asia/cambodia/data/admin.ts"
)


LEVELS = [
    {
        "label": "Province",
        "input": GEOJSON_DIR / "provinces.geojson",
        "constant": "CAMBODIA_PROVINCE_QUESTIONS",
        "id_property": "province_id",
        "display_property": "province",
        "native_property": "province_native",
    },
    {
        "label": "District",
        "input": GEOJSON_DIR / "districts.geojson",
        "constant": "CAMBODIA_DISTRICT_QUESTIONS",
        "id_property": "district_id",
        "display_property": "district",
        "native_property": "district_native",
    },
    {
        "label": "Commune",
        "input": GEOJSON_DIR / "communes.geojson",
        "constant": "CAMBODIA_COMMUNE_QUESTIONS",
        "id_property": "commune_id",
        "display_property": "commune",
        "native_property": None,
    },
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def ts_string(value: str) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def build_questions(
    config: dict[str, Any],
) -> list[dict[str, str]]:
    data = load_json(config["input"])

    questions: list[dict[str, str]] = []

    for feature in data["features"]:
        properties = feature["properties"]

        answer = str(
            properties[config["id_property"]]
        ).strip()

        display = str(
            properties[config["display_property"]]
        ).strip()

        question = {
            "answer": answer,
            "display": display,
        }

        native_property = config["native_property"]

        if native_property is not None:
            native_display = str(
                properties[native_property]
            ).strip()

            if not native_display:
                raise ValueError(
                    f"Missing {native_property} for {answer}"
                )

            question["nativeDisplay"] = native_display

        questions.append(question)

    questions.sort(
        key=lambda question: question["answer"]
    )

    return questions


def validate_questions(
    label: str,
    questions: list[dict[str, str]],
) -> None:
    answers = [
        question["answer"]
        for question in questions
    ]

    if len(answers) != len(set(answers)):
        raise ValueError(
            f"{label} questions contain duplicate answers."
        )


def render_question(
    question: dict[str, str],
) -> str:
    lines = [
        "  {",
        f'    answer: {ts_string(question["answer"])},',
        f'    display: {ts_string(question["display"])},',
    ]

    if "nativeDisplay" in question:
        lines.append(
            "    nativeDisplay: "
            f'{ts_string(question["nativeDisplay"])},'
        )

    lines.append("  },")

    return "\n".join(lines)


def render_array(
    constant: str,
    questions: list[dict[str, str]],
) -> str:
    rendered_questions = "\n".join(
        render_question(question)
        for question in questions
    )

    return (
        f"export const {constant}: "
        "FeatureQuizQuestion[] = [\n"
        f"{rendered_questions}\n"
        "];"
    )


def main() -> None:
    generated: list[
        tuple[dict[str, Any], list[dict[str, str]]]
    ] = []

    for config in LEVELS:
        questions = build_questions(config)

        validate_questions(
            config["label"],
            questions,
        )

        generated.append(
            (config, questions)
        )

    sections = [
        (
            "/**\n"
            " * Cambodia administrative quiz question data.\n"
            " *\n"
            " * Generated from GeoPedia's finalized Cambodia "
            "administrative GeoJSON files.\n"
            " * Provinces and districts include Khmer native "
            "labels; communes intentionally do not.\n"
            " *\n"
            " * Regenerate with:\n"
            " * python scripts/countries/asia/cambodia/"
            "generate/admin.py\n"
            " */"
        ),
        'import type { FeatureQuizQuestion } from "@/types/quiz";',
    ]

    for config, questions in generated:
        sections.append(
            render_array(
                config["constant"],
                questions,
            )
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        "\n\n".join(sections) + "\n",
        encoding="utf-8",
    )

    print("Cambodia administrative quiz data generated.")
    print()

    for config, questions in generated:
        print(
            f"{config['label'] + 's':<10} "
            f"{len(questions):>5,} questions"
        )

    print()
    print(
        OUTPUT_PATH.relative_to(PROJECT_ROOT)
    )


if __name__ == "__main__":
    main()