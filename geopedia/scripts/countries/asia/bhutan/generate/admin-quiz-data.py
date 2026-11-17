
"""
Generate GeoPedia Bhutan administrative quiz question data.

Inputs:
  public/data/countries/bhutan/geojson/
    bhutan_adm1.geojson
    bhutan_adm2.geojson

Output:
  src/quiz/quizzes/countries/asia/bhutan/data/admin.ts

Questions:
- ADM1: 20 dzongkhags with English and Dzongkha names.
- ADM2: 205 gewogs with English names only.
- Answers use the unique GeoJSON feature IDs.

Run from the GeoPedia project root:
  python scripts/countries/asia/bhutan/generate/generate-questions.py
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]

GEOJSON_DIR = (
    ROOT / "public/data/countries/bhutan/geojson"
)

OUTPUT_PATH = (
    ROOT
    / "src/quiz/quizzes/countries/asia/bhutan/data/admin.ts"
)

EXPECTED_COUNTS = {
    1: 20,
    2: 205,
}


def load_features(level):
    path = GEOJSON_DIR / f"bhutan_adm{level}.geojson"

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    features = data["features"]

    expected = EXPECTED_COUNTS[level]

    if len(features) != expected:
        raise ValueError(
            f"ADM{level}: expected {expected} features, "
            f"found {len(features)}"
        )

    return features


def validate_features(features, level):
    ids = set()

    for feature in features:
        feature_id = feature.get("id")
        properties = feature.get("properties", {})

        if not feature_id:
            raise ValueError(
                f"ADM{level}: feature missing ID"
            )

        if feature_id in ids:
            raise ValueError(
                f"ADM{level}: duplicate ID {feature_id}"
            )

        ids.add(feature_id)

        if not properties.get("name"):
            raise ValueError(
                f"ADM{level}: missing English name for {feature_id}"
            )

        if level == 1 and not properties.get("nativeName"):
            raise ValueError(
                f"ADM1: missing Dzongkha name for {feature_id}"
            )

        if level == 2:
            if not properties.get("dzongkhag"):
                raise ValueError(
                    f"ADM2: missing parent dzongkhag for {feature_id}"
                )

            if not properties.get("dzongkhagId"):
                raise ValueError(
                    f"ADM2: missing parent dzongkhag ID for {feature_id}"
                )


def make_questions(features, include_native):
    questions = []

    for feature in sorted(
        features,
        key=lambda item: item["properties"]["name"].casefold(),
    ):
        properties = feature["properties"]

        question = {
            "answer": str(feature["id"]),
            "display": properties["name"],
        }

        if include_native:
            question["nativeDisplay"] = properties["nativeName"]

        questions.append(question)

    return questions


def format_questions(name, questions):
    lines = [
        f"export const {name}: FeatureQuizQuestion[] = ["
    ]

    for question in questions:
        fields = [
            f"answer: {json.dumps(question['answer'], ensure_ascii=False)}",
            f"display: {json.dumps(question['display'], ensure_ascii=False)}",
        ]

        if "nativeDisplay" in question:
            fields.append(
                "nativeDisplay: "
                + json.dumps(
                    question["nativeDisplay"],
                    ensure_ascii=False,
                )
            )

        lines.append("  { " + ", ".join(fields) + " },")

    lines.append("];")

    return "\n".join(lines)


def main():
    adm1 = load_features(1)
    adm2 = load_features(2)

    validate_features(adm1, 1)
    validate_features(adm2, 2)

    # Ensure every ADM2 parent refers to a valid ADM1 feature.
    adm1_ids = {feature["id"] for feature in adm1}

    for feature in adm2:
        parent_id = feature["properties"]["dzongkhagId"]

        if parent_id not in adm1_ids:
            raise ValueError(
                f"Unknown parent dzongkhag ID: {parent_id}"
            )

    adm1_questions = make_questions(
        adm1,
        include_native=True,
    )

    adm2_questions = make_questions(
        adm2,
        include_native=False,
    )

    sections = [
        'import type { FeatureQuizQuestion } from "@/quiz/types";',
        "",
        "// Bhutan — 20 Dzongkhags (ADM1)",
        format_questions(
            "bhutanDzongkhagQuestions",
            adm1_questions,
        ),
        "",
        "// Bhutan — 205 Gewogs (ADM2)",
        format_questions(
            "bhutanGewogQuestions",
            adm2_questions,
        ),
        "",
    ]

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        "\n".join(sections),
        encoding="utf-8",
    )

    print(f"ADM1 questions: {len(adm1_questions)}")
    print(f"ADM2 questions: {len(adm2_questions)}")
    print(f"ADM1 native names: {sum('nativeDisplay' in q for q in adm1_questions)}")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
