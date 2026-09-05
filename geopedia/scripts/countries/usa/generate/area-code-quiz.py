"""
Generates the GeoPedia US area-code quiz definition from the processed
US area-code GeoJSON.

Each area code remains its own quiz question even when several codes
share the same geographic feature.
"""

import json
from pathlib import Path


INPUT_FILE = Path(
    "public/data/us-area-codes.geojson"
)

OUTPUT_FILE = Path(
    "src/quiz/quizzes/usa/usAreaCodesQuiz.ts"
)


def main():
    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    area_codes = set()

    for feature in data["features"]:
        properties = feature.get(
            "properties",
            {},
        )

        for area_code in properties.get(
            "area_codes",
            [],
        ):
            area_codes.add(str(area_code))

    sorted_area_codes = sorted(
        area_codes,
        key=int,
    )

    question_lines = "\n".join(
        f'    {{ answer: "{area_code}" }},'
        for area_code in sorted_area_codes
    )

    output = f'''/**
 * Defines the United States telephone area-code quiz.
 *
 * Each area code is presented as an independent quiz question. Geographic
 * regions containing overlay codes can therefore be answered multiple
 * times as each associated area code appears during the quiz.
 */

import type {{ Quiz }} from "@/types/quiz";

/**
 * Quiz definition for identifying US telephone area codes.
 */
export const usAreaCodesQuiz: Quiz = {{
  id: "us-area-codes",
  name: "US Area Codes",
  mapId: "us-area-codes",
  answerProperty: "area_codes",

  questions: [
{question_lines}
  ],
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
        f"Generated {len(sorted_area_codes)} "
        "area-code questions."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()