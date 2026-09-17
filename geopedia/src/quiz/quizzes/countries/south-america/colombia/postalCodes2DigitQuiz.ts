/**
 * Quiz configuration for the first two digits of Colombia's postal codes.
 *
 * The first two digits identify the department associated with the postal code.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COLOMBIA_DEPARTMENTS_BY_ID } from "./data/admin";

const COLOMBIA_POSTAL_CODE_2_QUESTIONS: FeatureQuiz["questions"] =
  Object.keys(COLOMBIA_DEPARTMENTS_BY_ID).map((answer) => ({
    answer,
    display: `${answer}----`,
  }));

const COLOMBIA_POSTAL_CODES_2_DESCRIPTION =
  `Learn all ${COLOMBIA_POSTAL_CODE_2_QUESTIONS.length} Colombian 2-digit ` +
  `postal-code regions. Each question shows the first two digits of an ` +
  `otherwise 6-digit Colombian postal code.`;

export const colombiaPostalCodes2DigitQuiz: FeatureQuiz = {
  id: "colombia-postal-codes-2",
  name: "2-Digit Postal Codes",
  description: COLOMBIA_POSTAL_CODES_2_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-departments",

  answerProperty: "postal_code_2_digit",
  answerType: "single",

  questions: COLOMBIA_POSTAL_CODE_2_QUESTIONS,
};
