/**
 * Quiz configuration for Mexico's postal-code regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { MEXICO_STATES_BY_ID } from "./data/admin";
import { MEXICO_POSTAL_CODE_QUESTIONS } from "./data/postalCodes";

const MEXICO_POSTAL_CODES_DESCRIPTION =
  `Learn Mexico's ${MEXICO_POSTAL_CODE_QUESTIONS.length} 2-digit postal-code ` +
  `prefixes, which represent the first two digits of an otherwise 5-digit ` +
  `postal code. Filters let you practice prefixes by first digit or state.`;

export const mexicoPostalCodesQuiz: FeatureQuiz = {
  id: "mexico-postal-codes",
  name: "2 Digit Postal Codes",
  description: MEXICO_POSTAL_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-postal-codes",

  answerProperty: "postal_code_prefix",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "first_digit",
        label: "First Digit",
        valueType: "string",
      },
      {
        property: "state_ids",
        label: "State",
        valueType: "string-array",
        valueLabels: MEXICO_STATES_BY_ID,
      },
    ],
  },

  questions: MEXICO_POSTAL_CODE_QUESTIONS,
};
