"""
Generates Colombia's municipalities quiz configuration.

Source:
    public/data/countries/colombia/geojson/municipalities.geojson

Output:
    src/quizzes/countries/colombia/municipalitiesQuiz.ts

The processed municipality GeoJSON is the canonical source for municipality
IDs, names, and department membership. Regenerate this file whenever the
processed Colombia municipality data changes.
"""

import json
from pathlib import Path


SOURCE_PATH = Path(
    "public/data/countries/colombia/geojson/municipalities.geojson"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/colombia/municipalitiesQuiz.ts"
)


def quote(value: str) -> str:
    """Serialize a string as a valid TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def load_features() -> list[dict]:
    """Load and validate the processed Colombia municipality features."""
    data = json.loads(
        SOURCE_PATH.read_text(encoding="utf-8")
    )

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "Municipality GeoJSON is not a FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Municipality GeoJSON is missing its features array."
        )

    if len(features) != 1122:
        raise ValueError(
            f"Expected 1122 municipalities, found {len(features)}."
        )

    return features


def build_entries(
    features: list[dict],
) -> list[tuple[str, str, str]]:
    """
    Extract municipality ID, name, and parent department ID.

    Municipality IDs are stable five-digit identifiers produced by the
    administrative processor.
    """
    entries: list[tuple[str, str, str]] = []

    seen_ids: set[str] = set()

    for feature in features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "A municipality feature has invalid properties."
            )

        municipality_id = properties.get("id")
        department_id = properties.get("department_id")
        name = properties.get("name")

        if not isinstance(municipality_id, str) or not municipality_id:
            raise ValueError(
                "A municipality feature is missing its ID."
            )

        if not isinstance(department_id, str) or not department_id:
            raise ValueError(
                f"Municipality {municipality_id} is missing department_id."
            )

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"Municipality {municipality_id} is missing its name."
            )

        if municipality_id in seen_ids:
            raise ValueError(
                f"Duplicate municipality ID: {municipality_id}"
            )

        seen_ids.add(municipality_id)

        entries.append(
            (
                municipality_id,
                name.strip(),
                department_id,
            )
        )

    entries.sort(key=lambda entry: entry[0])

    return entries


def create_source(
    entries: list[tuple[str, str, str]],
) -> str:
    """Create the complete TypeScript municipalities quiz module."""
    dictionary_lines = "\n".join(
        f"  {quote(municipality_id)}: {quote(name)},"
        for municipality_id, name, _ in entries
    )

    return f'''import type {{ FeatureQuiz }} from "@/types/quiz";

import {{
  COLOMBIA_DEPARTMENT_NAMES_BY_ID,
}} from "./departmentsQuiz";

/**
 * Colombia's municipality names keyed by their five-digit municipality IDs.
 *
 * This dictionary is generated from the processed municipality GeoJSON and
 * should not be edited manually.
 */
export const COLOMBIA_MUNICIPALITY_NAMES_BY_ID = {{
{dictionary_lines}
}} as const;

/**
 * Questions for Colombia's municipalities quiz.
 */
const COLOMBIA_MUNICIPALITY_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(COLOMBIA_MUNICIPALITY_NAMES_BY_ID).map(
    ([answer, display]) => ({{
      answer,
      display,
    }}),
  );

/**
 * Description shown for Colombia's Municipalities quiz.
 */
const COLOMBIA_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${{COLOMBIA_MUNICIPALITY_QUESTIONS.length}} municipalities of ` +
  `Colombia, with department filtering to practice any desired subset.`;

/**
 * Quiz configuration for Colombia's municipalities.
 */
export const colombiaMunicipalitiesQuiz: FeatureQuiz = {{
  id: "colombia-municipalities",
  name: "Municipalities",
  description: COLOMBIA_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-municipalities",

  answerProperty: "id",
  answerType: "single",

  grouping: {{
    properties: [
      {{
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: COLOMBIA_DEPARTMENT_NAMES_BY_ID,
      }},
    ],
  }},

  baseMapLayers: {{
    subdivisionLabels: false,
  }},

  questions: COLOMBIA_MUNICIPALITY_QUESTIONS,
}};
'''


def main() -> None:
    """Generate Colombia's municipalities quiz configuration."""
    print("Generating Colombia municipalities quiz...")

    features = load_features()

    entries = build_entries(features)

    source = create_source(entries)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print(f"Municipalities: {len(entries)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()