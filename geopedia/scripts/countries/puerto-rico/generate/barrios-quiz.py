"""Generate the Puerto Rico barrios quiz configuration for GeoPedia.

The generator reads GeoPedia's processed Puerto Rico barrio and municipality
GeoJSON files and writes the complete TypeScript FeatureQuiz configuration.

Barrio IDs are used as quiz answers because barrio names are not unique.
Question displays use the barrio name by itself when that name is unique
across Puerto Rico. When a barrio name occurs more than once, the parent
municipality is appended to disambiguate it.

For example:

    San Antonio
    San Antonio (Caguas)

Some barrio names may still produce identical displays within the same
municipality. These are allowed because each question still has a unique
barrio ID as its answer.

Input:
    public/data/countries/puerto-rico/geojson/barrios.geojson
    public/data/countries/puerto-rico/geojson/municipalities.geojson

Output:
    src/quiz/quizzes/puerto-rico/barriosQuiz.ts
"""

import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]

BARRIOS_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "barrios.geojson"
)

MUNICIPALITIES_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "puerto-rico"
    / "geojson"
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "puerto-rico"
    / "barriosQuiz.ts"
)

EXPECTED_BARRIO_COUNT = 901
EXPECTED_MUNICIPALITY_COUNT = 78


def load_geojson(path: Path) -> dict:
    """Load a GeoJSON file and validate its top-level structure."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected FeatureCollection in {path}, "
            f"found {data.get('type')!r}."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(f"Missing or invalid features array in {path}.")

    return data


def load_municipality_names() -> dict[str, str]:
    """Load municipality names keyed by municipality ID."""
    data = load_geojson(MUNICIPALITIES_PATH)
    features = data["features"]

    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(features)}."
        )

    municipalities: dict[str, str] = {}

    for feature in features:
        properties = feature.get("properties") or {}

        municipality_id = str(
            properties.get("municipality_id", "")
        ).strip()

        name = str(properties.get("name", "")).strip()

        if not municipality_id:
            raise ValueError(
                "Municipality feature is missing municipality_id."
            )

        if not name:
            raise ValueError(
                f"Municipality {municipality_id} has a blank name."
            )

        if municipality_id in municipalities:
            raise ValueError(
                f"Duplicate municipality ID: {municipality_id}"
            )

        municipalities[municipality_id] = name

    return municipalities


def load_barrios(
    municipality_names: dict[str, str],
) -> list[dict[str, str]]:
    """Load and validate normalized barrio records."""
    data = load_geojson(BARRIOS_PATH)
    features = data["features"]

    if len(features) != EXPECTED_BARRIO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_BARRIO_COUNT} barrios, "
            f"found {len(features)}."
        )

    barrios: list[dict[str, str]] = []
    barrio_ids: set[str] = set()

    for feature in features:
        properties = feature.get("properties") or {}

        barrio_id = str(
            properties.get("barrio_id", "")
        ).strip()

        name = str(
            properties.get("name", "")
        ).strip()

        municipality_id = str(
            properties.get("municipality_id", "")
        ).strip()

        if not barrio_id:
            raise ValueError("Barrio feature is missing barrio_id.")

        if barrio_id in barrio_ids:
            raise ValueError(
                f"Duplicate barrio ID: {barrio_id}"
            )

        if not name:
            raise ValueError(
                f"Barrio {barrio_id} has a blank name."
            )

        if municipality_id not in municipality_names:
            raise ValueError(
                f"Barrio {barrio_id} references unknown municipality "
                f"{municipality_id!r}."
            )

        barrio_ids.add(barrio_id)

        barrios.append(
            {
                "barrio_id": barrio_id,
                "name": name,
                "municipality_id": municipality_id,
            }
        )

    barrios.sort(
        key=lambda barrio: (
            municipality_names[barrio["municipality_id"]],
            barrio["name"],
            barrio["barrio_id"],
        )
    )

    return barrios


def create_questions(
    barrios: list[dict[str, str]],
    municipality_names: dict[str, str],
) -> list[dict[str, str]]:
    """Create unambiguous quiz questions from barrio records."""
    name_counts = Counter(
        barrio["name"]
        for barrio in barrios
    )

    questions: list[dict[str, str]] = []

    for barrio in barrios:
        name = barrio["name"]
        municipality_id = barrio["municipality_id"]

        if name_counts[name] == 1:
            display = name
        else:
            municipality_name = municipality_names[municipality_id]
            display = f"{name} ({municipality_name})"

        questions.append(
            {
                "answer": barrio["barrio_id"],
                "display": display,
            }
        )

    return questions


def ts_string(value: str) -> str:
    """Encode a Python string as a TypeScript-compatible string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def format_questions(
    questions: list[dict[str, str]],
) -> str:
    """Format barrio questions as a TypeScript array."""
    lines: list[str] = [
        "const PUERTO_RICO_BARRIO_QUESTIONS = ["
    ]

    for question in questions:
        answer = ts_string(question["answer"])
        display = ts_string(question["display"])

        lines.append(
            f"  {{ answer: {answer}, display: {display} }},"
        )

    lines.append("];")

    return "\n".join(lines)


def create_quiz_file(
    questions: list[dict[str, str]],
) -> str:
    """Create the complete Puerto Rico barrios quiz TypeScript source."""
    formatted_questions = format_questions(questions)

    return f'''import type {{ FeatureQuiz }} from "@/types/quiz";

import {{ PUERTO_RICO_MUNICIPALITY_NAMES_BY_ID }} from "./municipalitiesQuiz";

/**
 * Questions for Puerto Rico's mapped barrios.
 *
 * Generated from GeoPedia's processed Puerto Rico barrio dataset.
 * Do not edit manually.
 */
{formatted_questions}

/**
 * Quiz configuration for Puerto Rico's mapped barrios.
 */
export const puertoRicoBarriosQuiz: FeatureQuiz = {{
  id: "puerto-rico-barrios",
  name: "Barrios",
  description: `Learn all ${{PUERTO_RICO_BARRIO_QUESTIONS.length}} mapped barrios of Puerto Rico, with filters that let you practice barrios by municipality.`,

  kind: "feature",
  mapId: "puerto-rico-barrios",

  answerProperty: "barrio_id",
  answerType: "single",

  baseMapLayers: {{
    subdivisionLabels: false,
  }},

  grouping: {{
    properties: [
      {{
        property: "municipality_id",
        label: "Municipality",
        valueType: "string",
        valueLabels: PUERTO_RICO_MUNICIPALITY_NAMES_BY_ID,
      }},
    ],
  }},

  questions: PUERTO_RICO_BARRIO_QUESTIONS,
}};
'''


def write_quiz_file(content: str) -> None:
    """Write the generated TypeScript quiz configuration."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )


def print_summary(
    barrios: list[dict[str, str]],
    questions: list[dict[str, str]],
) -> None:
    """Print a concise generation summary."""
    duplicate_name_count = sum(
        1
        for count in Counter(
            barrio["name"]
            for barrio in barrios
        ).values()
        if count > 1
    )

    disambiguated_question_count = sum(
        1
        for question, barrio in zip(questions, barrios)
        if question["display"] != barrio["name"]
    )

    print()
    print("Puerto Rico barrios quiz generated successfully.")
    print(f"Questions written: {len(questions)}")
    print(
        "Repeated barrio names: "
        f"{duplicate_name_count}"
    )
    print(
        "Questions disambiguated by municipality: "
        f"{disambiguated_question_count}"
    )
    print(f"Output: {OUTPUT_PATH}")
    print("Validation passed.")


def main() -> None:
    """Generate Puerto Rico's barrio quiz configuration."""
    print(
        f"Reading municipalities from {MUNICIPALITIES_PATH}"
    )

    municipality_names = load_municipality_names()

    print(f"Reading barrios from {BARRIOS_PATH}")

    barrios = load_barrios(
        municipality_names,
    )

    questions = create_questions(
        barrios,
        municipality_names,
    )

    if len(questions) != EXPECTED_BARRIO_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_BARRIO_COUNT} questions, "
            f"generated {len(questions)}."
        )

    content = create_quiz_file(
        questions,
    )

    write_quiz_file(content)

    print_summary(
        barrios,
        questions,
    )


if __name__ == "__main__":
    main()