/**
 * Quiz configuration for the first two digits of Paraguay's postal codes.
 *
 * The first two digits identify a department-level division, including
 * Asunción's capital district.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PARAGUAY_DEPARTMENTS_BY_ID } from "./data/admin";

const PARAGUAY_POSTAL_CODES_2_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  Object.keys(PARAGUAY_DEPARTMENTS_BY_ID).map((departmentId) => ({
    answer: departmentId,
    display: `${departmentId.slice(2)}----`,
  }));

const PARAGUAY_POSTAL_CODES_2_DIGIT_DESCRIPTION =
  `Learn all ${PARAGUAY_POSTAL_CODES_2_DIGIT_QUESTIONS.length} 2-digit postal ` +
  `prefixes used across Paraguay. Paraguay uses 6-digit postal codes, with ` +
  `the first 2 digits identifying the department or capital district. For example, ` +
  `Asunción uses the prefix 00, with codes such as 001001 and 001518.`;

export const paraguayPostalCodes2DigitQuiz: FeatureQuiz = {
  id: "paraguay-postal-prefixes",
  name: "2-Digit Postal Prefixes",
  description: PARAGUAY_POSTAL_CODES_2_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "paraguay-departments",

  answerProperty: "department_id",
  answerType: "single",

  questions: PARAGUAY_POSTAL_CODES_2_DIGIT_QUESTIONS,
};
