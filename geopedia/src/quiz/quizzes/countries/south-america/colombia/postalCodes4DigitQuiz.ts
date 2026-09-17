/**
 * Quiz configuration for the first four digits of Colombia's postal codes.
 *
 * Questions can be grouped by department for more focused practice. Bogotá is
 * represented by one combined question covering prefixes 1101 through 1120.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COLOMBIA_DEPARTMENTS_BY_ID } from "./data/admin";
import { COLOMBIA_POSTAL_CODE_4_QUESTIONS } from "./data/postalCodes";

const COLOMBIA_POSTAL_CODES_4_DESCRIPTION =
  `Learn all ${COLOMBIA_POSTAL_CODE_4_QUESTIONS.length} Colombian 4-digit ` +
  `postal-code regions. Each ordinary question represents the first four ` +
  `digits of an otherwise 6-digit postal code. Bogotá is represented by one ` +
  `combined 1101-1120 question because those prefixes divide the capital.`;

export const colombiaPostalCodes4DigitQuiz: FeatureQuiz = {
  id: "colombia-postal-codes-4",
  name: "4-Digit Postal Codes",
  description: COLOMBIA_POSTAL_CODES_4_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-postal-codes-4-digit",

  answerProperty: "postal_code_4_digit",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: COLOMBIA_DEPARTMENTS_BY_ID,
      },
    ],
  },

  questions: COLOMBIA_POSTAL_CODE_4_QUESTIONS,
};
