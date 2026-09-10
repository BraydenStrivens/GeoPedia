import type { FeatureQuiz } from "@/types/quiz";

import { COLOMBIA_DEPARTMENT_NAMES_BY_ID } from "./departmentsQuiz";

/**
 * Colombia's geographic fixed-line telephone codes.
 */
const COLOMBIA_PHONE_CODE_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "601" },
  { answer: "602" },
  { answer: "604" },
  { answer: "605" },
  { answer: "606" },
  { answer: "607" },
  { answer: "608" },
];

/**
 * Description shown for Colombia's Phone Codes quiz.
 */
const COLOMBIA_PHONE_CODES_DESCRIPTION =
  `Learn all ${COLOMBIA_PHONE_CODE_QUESTIONS.length} geographic fixed-line ` +
  `telephone codes used across Colombia. Colombian fixed-line numbers use a ` +
  `3-digit geographic code followed by a 7-digit local number, for 10 digits ` +
  `total, such as 601 XXX-XXXX in Bogotá or 604 XXX-XXXX in Antioquia. ` +
  `Mobile numbers instead begin with 3 and do not use these geographic codes.`;

/**
 * Quiz configuration for Colombia's geographic fixed-line telephone codes.
 */
export const colombiaPhoneCodesQuiz: FeatureQuiz = {
  id: "colombia-phone-codes",
  name: "Phone Codes",
  description: COLOMBIA_PHONE_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-phone-codes",

  answerProperty: "phone_code",
  answerType: "multiple",

  questions: COLOMBIA_PHONE_CODE_QUESTIONS,
};
