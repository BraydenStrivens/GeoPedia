"""
Generates the GeoPedia US Counties quiz from the processed county GeoJSON.

Each county uses its Census GEOID as the answer value so duplicate county
names across different states remain unambiguous.

The visible question includes both the county name and state name.
"""

import json
from pathlib import Path


INPUT_FILE = Path(
    "public/data/us-counties.geojson"
)

OUTPUT_FILE = Path(
    "src/quiz/quizzes/usa/usCountiesQuiz.ts"
)


def main():
    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    counties = []

    for feature in data["features"]:
        properties = feature[
            "properties"
        ]

        counties.append(
            {
                "answer": properties[
                    "geoid"
                ],
                "display": (
                    f'{properties["fullName"]}, '
                    f'{properties["stateName"]}'
                ),
            }
        )

    counties.sort(
        key=lambda county: (
            county["display"]
        )
    )

    question_lines = "\n".join(
        (
            f'    {{ answer: "{county["answer"]}", '
            f'display: '
            f'"{county["display"]}" }},'
        )
        for county in counties
    )

    output = f'''/**
 * Defines the United States counties quiz.
 *
 * Census GEOIDs are used as answer values so counties with duplicate names
 * remain uniquely identifiable. The visible question includes the county
 * and state name for nationwide play.
 */

import type {{ Quiz }} from "@/types/quiz";

export const usCountiesQuiz: Quiz = {{
  id: "us-counties",
  name: "US Counties",
  mapId: "us-counties",
  answerProperty: "geoid",
  answerType: "single",

  questions: [
{question_lines}
  ],
}};
'''

    OUTPUT_FILE.write_text(
        output,
        encoding="utf-8",
    )

    print(
        f"Generated "
        f"{len(counties)} county questions."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()