"""
Generates Colombia's 4-digit postal-code quiz configuration.

Source:
    public/data/countries/colombia/geojson/municipalities.geojson

Output:
    src/quizzes/countries/colombia/postalCodes4Quiz.ts

Municipality features may contain either one 4-digit postal prefix or multiple
prefixes. Bogotá is represented by one synthetic answer covering prefixes
1101 through 1120.
"""

import json
from pathlib import Path


SOURCE_PATH = Path(
    "public/data/countries/colombia/geojson/municipalities.geojson"
)

OUTPUT_PATH = Path(
    "src/quiz/quizzes/colombia/postalCodes4Quiz.ts"
)

BOGOTA_POSTAL_ANSWER = "bogota-1101-1120"


def quote(value: str) -> str:
    """Serialize a string as a valid TypeScript string literal."""
    return json.dumps(
        value,
        ensure_ascii=False,
    )


def load_features() -> list[dict]:
    """Load and validate Colombia's processed municipality GeoJSON."""
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


def extract_postal_answers(
    features: list[dict],
) -> list[str]:
    """
    Return every distinct logical 4-digit postal-code answer.

    String properties contribute one answer. Array properties contribute one
    answer for each represented postal prefix.
    """
    answers: set[str] = set()

    for feature in features:
        properties = feature.get("properties")

        if not isinstance(properties, dict):
            raise ValueError(
                "A municipality feature has invalid properties."
            )

        municipality_id = properties.get("id")

        value = properties.get("postal_code_4_digit")

        if isinstance(value, str):
            answers.add(value)

        elif isinstance(value, list):
            for answer in value:
                if not isinstance(answer, str) or not answer:
                    raise ValueError(
                        f"Municipality {municipality_id} has an invalid "
                        "postal-code prefix."
                    )

                answers.add(answer)

        else:
            raise ValueError(
                f"Municipality {municipality_id} has an invalid "
                "postal_code_4_digit property."
            )

    if BOGOTA_POSTAL_ANSWER not in answers:
        raise ValueError(
            "Expected Bogotá synthetic postal answer was not found."
        )

    return sorted(
        answers,
        key=lambda answer: (
            answer == BOGOTA_POSTAL_ANSWER,
            answer,
        ),
    )


def get_display(answer: str) -> str:
    """Return the user-facing display text for one postal answer."""
    if answer == BOGOTA_POSTAL_ANSWER:
        return "1101–1120"

    if len(answer) != 4 or not answer.isdigit():
        raise ValueError(
            f"Unexpected postal answer: {answer}"
        )

    return f"{answer}--"


def create_source(
    answers: list[str],
) -> str:
    """Create the TypeScript 4-digit postal-code quiz module."""
    question_lines = "\n".join(
        "\n".join(
            [
                "  {",
                f"    answer: {quote(answer)},",
                f"    display: {quote(get_display(answer))},",
                "  },",
            ]
        )
        for answer in answers
    )

    return f'''import type {{ FeatureQuiz }} from "@/types/quiz";

import {{
  COLOMBIA_DEPARTMENT_NAMES_BY_ID,
}} from "./departmentsQuiz";

/**
 * Questions for Colombia's 4-digit postal-code prefix quiz.
 *
 * Bogotá is represented by one logical answer covering prefixes 1101 through
 * 1120. Other questions represent one ordinary 4-digit prefix.
 *
 * This list is generated from the processed municipality GeoJSON and should
 * not be edited manually.
 */
const COLOMBIA_POSTAL_CODE_4_QUESTIONS: FeatureQuiz["questions"] = [
{question_lines}
];

/**
 * Description shown for Colombia's 4-Digit Postal Codes quiz.
 */
const COLOMBIA_POSTAL_CODES_4_DESCRIPTION =
  `Learn all ${{COLOMBIA_POSTAL_CODE_4_QUESTIONS.length}} Colombian 4-digit ` +
  `postal-code regions. Each ordinary question represents the first four ` +
  `digits of an otherwise 6-digit postal code. Bogotá is represented by one ` +
  `combined 1101–1120 question because those prefixes divide the capital ` +
  `rather than following municipality boundaries.`;

/**
 * Quiz configuration for Colombia's 4-digit postal-code prefixes.
 */
export const colombiaPostalCodes4Quiz: FeatureQuiz = {{
  id: "colombia-postal-codes-4",
  name: "4-Digit Postal Codes",
  description: COLOMBIA_POSTAL_CODES_4_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-municipalities",

  answerProperty: "postal_code_4_digit",
  answerType: "multiple",

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

  questions: COLOMBIA_POSTAL_CODE_4_QUESTIONS,
}};
'''


def main() -> None:
    """Generate Colombia's 4-digit postal-code quiz configuration."""
    print("Generating Colombia 4-digit postal-code quiz...")

    features = load_features()

    answers = extract_postal_answers(features)

    source = create_source(answers)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print(f"Questions: {len(answers)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()