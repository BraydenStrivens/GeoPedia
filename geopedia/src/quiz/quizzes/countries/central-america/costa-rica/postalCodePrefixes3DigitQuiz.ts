/**
 * Quiz for identifying Costa Rica's 3-digit postal-code prefixes.
 *
 * Each prefix corresponds to a canton and represents the first three digits
 * of Costa Rica's 5-digit postal codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  COSTA_RICA_CANTONS_BY_ID,
  COSTA_RICA_PROVINCES_BY_ID,
} from "./data/admin";

const COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  Object.keys(COSTA_RICA_CANTONS_BY_ID).map((answer) => ({
    answer,
    display: `${answer}--`,
  }));

const COSTA_RICA_POSTAL_CODE_PREFIXES_3_DIGIT_DESCRIPTION =
  `Learn Costa Rica's ${COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS.length} ` +
  `3-digit postal-code prefixes, which represent the first three digits of an ` +
  `otherwise 5-digit postal code. Filters let you practice prefixes by province.`;

export const costaRicaPostalCodePrefixes3DigitQuiz: FeatureQuiz = {
  id: "costa-rica-postal-code-prefixes-3-digit",
  name: "3 Digit Postal Codes",
  description: COSTA_RICA_POSTAL_CODE_PREFIXES_3_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "costa-rica-cantons",

  answerProperty: "canton_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: COSTA_RICA_PROVINCES_BY_ID,
      },
    ],
  },

  questions: COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS,
};
