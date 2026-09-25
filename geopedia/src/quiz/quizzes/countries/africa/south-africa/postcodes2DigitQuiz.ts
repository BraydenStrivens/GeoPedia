/**
 * South Africa two-digit postcode-prefix feature quiz.
 *
 * Questions are generated directly from the runtime two-digit postcode
 * geography.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_POSTCODES_2_QUIZ_QUESTIONS } from "./data/postcodes";

const DESCRIPTION =
  `Learn the 2-digit postal code prefixes of South Africa.\n\n` +
  `South African postal codes contain four digits, and this quiz uses their ` +
  `first two digits. For example, postal code 2760 in Agisanang begins with ` +
  `27 and 6282 in Adendorp begins with 62. You can group the ` +
  `quiz by the first digit to study one broad postal region at a time.`;

export const southAfricaPostcodes2DigitQuiz: FeatureQuiz = {
  id: "south-africa-postcodes-2",
  name: "2-Digit Postcode Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-postcodes-2",

  answerProperty: "prefix_2",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "prefix_1",
        label: "1-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: SOUTH_AFRICA_POSTCODES_2_QUIZ_QUESTIONS,
};
