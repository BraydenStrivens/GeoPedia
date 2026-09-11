from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_PATH = (
    PROJECT_ROOT
    / "public"
    / "data"
    / "countries"
    / "brazil"
    / "geojson"
    / "municipalities.geojson"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "src"
    / "quiz"
    / "quizzes"
    / "country"
    / "brazil"
    / "municipalitiesQuiz.ts"
)

EXPECTED_MUNICIPALITY_COUNT = 5573


def load_geojson(path: Path) -> dict[str, Any]:
    """Load a GeoJSON file from disk."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_municipalities(features: list[dict[str, Any]]) -> None:
    """Validate the processed Brazil municipality features used by the quiz."""
    if len(features) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MUNICIPALITY_COUNT} municipalities, "
            f"found {len(features)}."
        )

    seen_ids: set[str] = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {index} is missing a valid properties object."
            )

        municipality_id = properties.get("id")
        name = properties.get("name")
        state_id = properties.get("state_id")

        if not isinstance(municipality_id, str) or not municipality_id:
            raise ValueError(
                f"Feature {index} has an invalid municipality id."
            )

        if not isinstance(name, str) or not name:
            raise ValueError(
                f"Municipality {municipality_id} has an invalid name."
            )

        if not isinstance(state_id, str) or not state_id:
            raise ValueError(
                f"Municipality {municipality_id} has an invalid state_id."
            )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality id found: {municipality_id}"
            )

        seen_ids.add(municipality_id)


def escape_typescript_string(value: str) -> str:
    """Escape a string for use inside a double-quoted TypeScript string."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def build_names_dictionary(
    features: list[dict[str, Any]],
) -> str:
    """Build the municipality ID-to-name TypeScript dictionary."""
    lines: list[str] = []

    for feature in features:
        properties = feature["properties"]

        municipality_id = escape_typescript_string(properties["id"])
        name = escape_typescript_string(properties["name"])

        lines.append(f'  "{municipality_id}": "{name}",')

    return "\n".join(lines)


def build_quiz_file(features: list[dict[str, Any]]) -> str:
    """Build the complete Brazil municipalities quiz TypeScript source."""
    names_dictionary = build_names_dictionary(features)

    return f'''import type {{ FeatureQuiz }} from "@/types/quiz";

import {{ BRAZIL_STATE_NAMES_BY_ID }} from "./statesQuiz";

/**
 * Brazil's municipality names keyed by their official seven-digit IBGE
 * municipality IDs.
 *
 * This dictionary is generated from the processed municipality GeoJSON and
 * should not be edited manually.
 */
export const BRAZIL_MUNICIPALITY_NAMES_BY_ID = {{
{names_dictionary}
}} as const;

/**
 * Questions for Brazil's Municipalities quiz.
 */
const BRAZIL_MUNICIPALITY_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BRAZIL_MUNICIPALITY_NAMES_BY_ID).map(
    ([answer, display]) => ({{
      answer,
      display,
    }}),
  );

/**
 * Description shown for Brazil's Municipalities quiz.
 */
const BRAZIL_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${{BRAZIL_MUNICIPALITY_QUESTIONS.length}} municipalities of ` +
  `Brazil, with state filtering to practice any desired subset.`;

/**
 * Quiz configuration for Brazil's municipalities.
 */
export const brazilMunicipalitiesQuiz: FeatureQuiz = {{
  id: "brazil-municipalities",
  name: "Municipalities",
  description: BRAZIL_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-municipalities",

  answerProperty: "id",
  answerType: "single",

  grouping: {{
    properties: [
      {{
        property: "state_id",
        label: "State",
        valueType: "string",
        valueLabels: BRAZIL_STATE_NAMES_BY_ID,
      }},
    ],
  }},

  questions: BRAZIL_MUNICIPALITY_QUESTIONS,
}};
'''


def main() -> None:
    """Generate Brazil's municipality quiz config from runtime GeoJSON."""
    print("Loading Brazil municipality GeoJSON...")

    geojson = load_geojson(INPUT_PATH)

    features = geojson.get("features")

    if not isinstance(features, list):
        raise ValueError("Input GeoJSON is missing a valid features array.")

    print("Validating municipalities...")
    validate_municipalities(features)

    print("Generating TypeScript quiz config...")
    output = build_quiz_file(features)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(output, encoding="utf-8")

    print()
    print("Brazil municipality quiz generation complete.")
    print(f"Municipalities: {len(features):,}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()