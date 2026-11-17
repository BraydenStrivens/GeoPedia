"""Generate Bangladesh ADM1–ADM3 quiz questions and map-ready ID properties.

Input:
  public/data/countries/bangladesh/geojson/bangladesh_adm{1,2,3}.geojson

Outputs:
  Updates the input GeoJSON files to include properties.admin_id, copied from
  each feature's existing top-level shapeID-derived id (id is preserved).
  src/quiz/quizzes/countries/asia/bangladesh/data/admin.ts

Questions use stable IDs as answers, English names as display, and Bengali
nativeDisplay for ADM1 and ADM2. Duplicate English names are qualified by
parent district/division to avoid ambiguous question prompts.

Run from project root:
  python scripts/countries/asia/bangladesh/generate/admin_quiz_data.py

Dependencies: Python standard library only.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
GEOJSON = ROOT / "public/data/countries/bangladesh/geojson"
OUTPUT = ROOT / "src/quiz/quizzes/countries/asia/bangladesh/data/admin.ts"
LEVELS = (
    (1, "BANGLADESH_DIVISION_QUESTIONS", 8),
    (2, "BANGLADESH_DISTRICT_QUESTIONS", 64),
    (3, "BANGLADESH_UPAZILA_QUESTIONS", 544),
)


def load_and_prepare(level: int, expected: int) -> list[dict]:
    path = GEOJSON / f"bangladesh_adm{level}.geojson"
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data["features"]
    if len(features) != expected:
        raise ValueError(f"ADM{level}: expected {expected}, got {len(features)}")
    ids = []
    changed = False
    for feature in features:
        fid = str(feature["id"])
        props = feature["properties"]
        if not fid or not props.get("name"):
            raise ValueError(f"ADM{level}: missing ID or name")
        if level <= 2 and not props.get("nativeName"):
            raise ValueError(f"ADM{level} {fid}: missing Bengali name")
        if level >= 2 and not props.get("division"):
            raise ValueError(f"ADM{level} {fid}: missing division")
        if level == 3 and not props.get("district"):
            raise ValueError(f"ADM3 {fid}: missing district")
        if "admin_id" in props and props["admin_id"] != fid:
            raise ValueError(f"ADM{level} {fid}: conflicting admin_id")
        if "admin_id" not in props:
            props["admin_id"] = fid
            changed = True
        ids.append(fid)
    if len(ids) != len(set(ids)):
        raise ValueError(f"ADM{level}: duplicate IDs")
    if changed:
        path.write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    return features


def build_questions(features: list[dict], level: int) -> list[dict]:
    counts = Counter(f["properties"]["name"].casefold() for f in features)
    questions = []
    for feature in features:
        props = feature["properties"]
        name = props["name"]
        display = name
        if counts[name.casefold()] > 1:
            parent = props["district"] if level == 3 else props.get("division")
            if not parent:
                raise ValueError(f"ADM{level} duplicate {name!r} lacks parent")
            display = f"{name} ({parent})"
        question = {"answer": props["admin_id"], "display": display}
        if level <= 2:
            question["nativeDisplay"] = props["nativeName"]
        questions.append(question)
    questions.sort(key=lambda q: (q["display"].casefold(), q["answer"]))
    return questions


def main() -> None:
    sections = [
        "/** Generated Bangladesh administrative quiz questions. Do not edit manually. */",
        'import type { FeatureQuizQuestion } from "@/types/quiz";',
        "",
    ]
    for level, constant, expected in LEVELS:
        features = load_and_prepare(level, expected)
        questions = build_questions(features, level)
        serialized = json.dumps(questions, ensure_ascii=False, indent=2)
        sections.append(
            f"export const {constant}: FeatureQuizQuestion[] = {serialized};"
        )
        sections.append("")
        print(f"ADM{level}: {len(questions)} questions generated")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(sections), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
