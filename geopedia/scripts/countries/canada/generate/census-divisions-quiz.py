"""
Generates the GeoPedia Canada Census Divisions quiz from the processed
Statistics Canada census division GeoJSON.

Each census division uses its Census Division Unique Identifier (CDUID) as
the answer value so divisions remain uniquely identifiable even if names are
duplicated across provinces or territories.

The visible question includes both the census division name and its province
or territory. The generated FeatureQuiz also supports grouping questions by
province or territory.
"""

import json
from pathlib import Path


INPUT_FILE = Path(
    "public/data/countries/canada/geojson/census-divisions.geojson"
)

OUTPUT_FILE = Path(
    "src/quiz/quizzes/canada/canadaCensusDivisionsQuiz.ts"
)

EXPECTED_FEATURE_COUNT = 293

REQUIRED_PROPERTIES = (
    "cduid",
    "name",
    "province",
)


def get_required_property(
    properties: dict,
    property_name: str,
    feature_index: int,
) -> str:
    """
    Returns a required non-empty string property from a GeoJSON feature.

    Raises a ValueError with the feature index when the property is missing
    or invalid so malformed processed data cannot silently produce a broken
    quiz configuration.
    """
    value = properties.get(property_name)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f'Feature {feature_index} has invalid or missing '
            f'"{property_name}".'
        )

    return value.strip()
  
def should_include_province_in_display(name: str) -> bool:
    """
    Returns whether a census division name is generic enough that the
    province or territory should be included in the visible question.
    """
    normalized_name = name.lower()

    return (
        normalized_name.startswith("division no.")
        or normalized_name.startswith("region ")
    )


def build_questions(features: list[dict]) -> list[dict]:
    """
    Converts processed census division features into quiz questions.

    CDUID is used as the answer value while the displayed question contains
    both the division name and province or territory.
    """
    questions = []
    seen_cduids = set()

    for index, feature in enumerate(features):
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                f"Feature {index} is missing a valid properties object."
            )

        values = {
            property_name: get_required_property(
                properties,
                property_name,
                index,
            )
            for property_name in REQUIRED_PROPERTIES
        }

        cduid = values["cduid"]
        name = values["name"]
        province = values["province"]

        if cduid in seen_cduids:
            raise ValueError(
                f'Duplicate CDUID "{cduid}" found in processed GeoJSON.'
            )

        seen_cduids.add(cduid)
        
        display = (
          f"{name}, {province}"
          if should_include_province_in_display(name)
          else name
      )

        questions.append(
            {
                "answer": cduid,
                "display": display,
            }
        )

    questions.sort(
        key=lambda question: question["display"]
    )

    return questions


def to_typescript_string(value: str) -> str:
    """
    Converts a Python string into a safely escaped TypeScript string literal.
    """
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def generate_question_lines(
    questions: list[dict],
) -> str:
    """
    Formats quiz questions as TypeScript object literals.
    """
    return "\n".join(
        (
            "    { "
            f"answer: {to_typescript_string(question['answer'])}, "
            f"display: {to_typescript_string(question['display'])} "
            "},"
        )
        for question in questions
    )


def main():
    """
    Reads the processed Canada census division GeoJSON, validates it, and
    writes the generated FeatureQuiz TypeScript configuration.
    """
    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Input GeoJSON does not contain a valid features array."
        )

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} census divisions, "
            f"found {len(features)}."
        )

    questions = build_questions(features)

    if len(questions) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_FEATURE_COUNT} generated questions, "
            f"found {len(questions)}."
        )

    question_lines = generate_question_lines(
        questions
    )

    output = f'''/**
 * Defines the Canada Census Divisions quiz.
 *
 * Statistics Canada CDUIDs are used as answer values so every census
 * division remains uniquely identifiable. Visible questions include both
 * the census division name and its province or territory.
 *
 * Questions are generated from the processed census division GeoJSON and
 * can be grouped by province or territory.
 */
import type {{ FeatureQuiz }} from "@/types/quiz";

const CANADA_CENSUS_DIVISION_QUESTIONS = [
{question_lines}
];

const CANADA_CENSUS_DIVISIONS_DESCRIPTION =
  `Learn ${{CANADA_CENSUS_DIVISION_QUESTIONS.length}} census divisions across Canada, including counties, regional districts, regional county municipalities, and other county-equivalent statistical regions.`;

export const canadaCensusDivisionsQuiz: FeatureQuiz = {{
  id: "canada-census-divisions",
  name: "Canada Census Divisions",
  description: CANADA_CENSUS_DIVISIONS_DESCRIPTION,
  kind: "feature",
  mapId: "canada-census-divisions",
  answerProperty: "cduid",
  answerType: "single",
  baseMapLayers: {{
    subdivisionLabels: false,
  }},
  grouping: {{
    properties: [
      {{
        property: "province",
        label: "Province / Territory",
        valueType: "string",
      }},
    ],
  }},
  questions: CANADA_CENSUS_DIVISION_QUESTIONS,
}};
'''

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        output,
        encoding="utf-8",
    )

    print(
        f"Generated {len(questions)} census division questions."
    )
    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()