import type { FeatureQuiz } from "@/types/quiz";

import { COLOMBIA_DEPARTMENT_NAMES_BY_ID } from "./departmentsQuiz";

/**
 * Questions for Colombia's two-digit postal-code prefix quiz.
 */
const COLOMBIA_POSTAL_CODE_2_QUESTIONS: FeatureQuiz["questions"] =
  Object.keys(COLOMBIA_DEPARTMENT_NAMES_BY_ID).map((answer) => ({
    answer,
    display: `${answer}----`,
  }));

/**
 * Description shown for Colombia's 2-Digit Postal Codes quiz.
 */
const COLOMBIA_POSTAL_CODES_2_DESCRIPTION =
  `Learn all ${COLOMBIA_POSTAL_CODE_2_QUESTIONS.length} Colombian 2-digit ` +
  `postal-code regions. Each question shows the first two digits of an ` +
  `otherwise 6-digit Colombian postal code.`;

/**
 * Quiz configuration for Colombia's two-digit postal-code prefixes.
 */
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
