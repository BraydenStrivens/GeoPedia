/**
 * Quiz for identifying Costa Rica's 1-digit postal-code prefixes.
 *
 * Each prefix corresponds to a province and represents the first digit
 * of Costa Rica's 5-digit postal codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COSTA_RICA_PROVINCES_BY_ID } from "./data/admin";

/**
 * Questions for Costa Rica's 1-digit postal-code prefixes.
 *
 * Four trailing dashes show each prefix's position within a 5-digit
 * postal code.
 */
const COSTA_RICA_POSTAL_CODE_PREFIX_1_DIGIT_QUESTIONS = Object.keys(
  COSTA_RICA_PROVINCES_BY_ID,
).map((answer) => ({
  answer,
  display: `${answer}----`,
}));

const COSTA_RICA_POSTAL_CODE_PREFIXES_1_DIGIT_DESCRIPTION =
  `Learn Costa Rica's ${COSTA_RICA_POSTAL_CODE_PREFIX_1_DIGIT_QUESTIONS.length} ` +
  `1-digit postal-code prefixes, which represent the first digit of an ` +
  `otherwise 5-digit postal code.`;

export const costaRicaPostalCodePrefixes1DigitQuiz: FeatureQuiz = {
  id: "costa-rica-postal-code-prefixes-1-digit",
  name: "1 Digit Postal Codes",
  description: COSTA_RICA_POSTAL_CODE_PREFIXES_1_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "costa-rica-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: COSTA_RICA_POSTAL_CODE_PREFIX_1_DIGIT_QUESTIONS,
};
