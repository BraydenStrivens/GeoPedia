/**
 * South Africa three-digit postcode-prefix feature quiz.
 *
 * Questions are generated directly from the runtime three-digit postcode
 * geography.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_POSTCODES_3_QUIZ_QUESTIONS } from "./data/postcodes";

const DESCRIPTION =
  `Learn the 3-digit postal code prefixes of South Africa.\n\n` +
  `South African postal codes contain four digits. In this quiz, only the ` +
  `first three digits are used. For example, postal code 1055 in Middelburg ` +
  `has the prefix 105 and 5760 in Adelaide has the prefix 576.` +
  `You can group the quiz by its broader 1- or 2-digit prefixes.`;

export const southAfricaPostcodes3DigitQuiz: FeatureQuiz = {
  id: "south-africa-postcodes-3",
  name: "3-Digit Postcode Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-postcodes-3",

  answerProperty: "prefix_3",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "prefix_1",
        label: "1-Digit Prefix",
        valueType: "string",
      },
      {
        property: "prefix_2",
        label: "2-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: SOUTH_AFRICA_POSTCODES_3_QUIZ_QUESTIONS,
};
