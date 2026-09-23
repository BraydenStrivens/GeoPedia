/**
 * Feature quiz for Kenya's 3-digit postal-code prefixes.
 *
 * Questions use the individual postal prefixes as answers. Some prefixes share
 * the same postal-region geometry, so the map's postal_prefixes property
 * provides multiple accepted answers for those features.
 *
 * Questions can be grouped by their first digit.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { KENYA_POSTAL_3_DIGIT_QUESTIONS } from "./data/postalCodes";

const DESCRIPTION =
  `Learn all ${KENYA_POSTAL_3_DIGIT_QUESTIONS.length} 3-digit postal-code ` +
  `prefixes of Kenya. Kenyan postal codes contain five digits, so a prefix ` +
  `such as 301-- represents postal codes beginning with 301. For example, ` +
  `10100 is Nyeri, 30100 is Eldoret, 50100 is Kakamega, and 80200 is Malindi.`;

export const kenyaPostal3DigitPrefixesQuiz: FeatureQuiz = {
  id: "kenya-postal-3-digit-prefixes",
  name: "3-Digit Postal Codes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "kenya-postal-3-digit-prefixes",

  answerProperty: "postal_prefixes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "first_digit",
        label: "First Digit",
        valueType: "string",
      },
    ],
  },

  questions: KENYA_POSTAL_3_DIGIT_QUESTIONS,
};
