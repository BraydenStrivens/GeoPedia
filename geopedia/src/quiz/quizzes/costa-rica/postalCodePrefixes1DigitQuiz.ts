import type { FeatureQuiz } from "@/types/quiz";

import { COSTA_RICA_PROVINCE_NAMES_BY_ID } from "./provincesQuiz";

/**
 * Questions for Costa Rica's 1-digit postal-code prefixes.
 *
 * Four trailing dashes show each prefix's position within a 5-digit
 * postal code.
 */
const COSTA_RICA_POSTAL_CODE_PREFIX_1_DIGIT_QUESTIONS = Object.keys(
  COSTA_RICA_PROVINCE_NAMES_BY_ID,
).map((answer) => ({
  answer,
  display: `${answer}----`,
}));

/**
 * Tests Costa Rica's 1-digit postal-code prefixes.
 */
export const costaRicaPostalCodePrefixes1DigitQuiz: FeatureQuiz = {
  id: "costa-rica-postal-code-prefixes-1-digit",
  name: "1 Digit Postal Codes",
  description: `Learn Costa Rica's ${COSTA_RICA_POSTAL_CODE_PREFIX_1_DIGIT_QUESTIONS.length} 1-digit postal-code prefixes, which represent the first digit of an otherwise 5-digit postal code.`,

  kind: "feature",
  mapId: "costa-rica-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: COSTA_RICA_POSTAL_CODE_PREFIX_1_DIGIT_QUESTIONS,
};
