import { COSTA_RICA_CANTON_NAMES_BY_ID } from "./cantonsQuiz";
import { COSTA_RICA_PROVINCE_NAMES_BY_ID } from "./provincesQuiz";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * Questions for Costa Rica's 3-digit postal-code prefixes.
 *
 * Two trailing dashes show each prefix's position within a 5-digit
 * postal code.
 */
const COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS = Object.keys(
  COSTA_RICA_CANTON_NAMES_BY_ID,
).map((answer) => ({
  answer,
  display: `${answer}--`,
}));

/**
 * Tests Costa Rica's 3-digit postal-code prefixes.
 *
 * Each prefix corresponds to a canton and represents the first three digits
 * of Costa Rica's otherwise 5-digit postal codes.
 */
export const costaRicaPostalCodePrefixes3DigitQuiz: FeatureQuiz = {
  id: "costa-rica-postal-code-prefixes-3-digit",
  name: "3 Digit Postal Codes",
  description: `Learn Costa Rica's ${COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS.length} 3-digit postal-code prefixes, which represent the first three digits of an otherwise 5-digit postal code. Filters let you practice prefixes by province.`,

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
        valueLabels: COSTA_RICA_PROVINCE_NAMES_BY_ID,
      },
    ],
  },

  questions: COSTA_RICA_POSTAL_CODE_PREFIX_3_DIGIT_QUESTIONS,
};
