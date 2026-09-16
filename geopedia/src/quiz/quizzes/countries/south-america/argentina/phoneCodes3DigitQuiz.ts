/**
 * Quiz configuration for Argentina's three-digit geographic telephone-code
 * regions.
 *
 * Four-digit area codes are grouped by their first three digits, while
 * complete two- and three-digit area codes remain unchanged.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ARGENTINA_PHONE_CODES_3_DIGIT } from "./data/phoneCodes";

const ARGENTINA_PHONE_CODES_3_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  ARGENTINA_PHONE_CODES_3_DIGIT.map((areaCode) => ({
    answer: areaCode,
  }));

const ARGENTINA_PHONE_CODES_3_DIGIT_DESCRIPTION =
  `Learn all ${ARGENTINA_PHONE_CODES_3_DIGIT_QUESTIONS.length} three-digit ` +
  `telephone-code regions of Argentina. Argentine geographic telephone numbers ` +
  `include the area code plus subscriber number, they always ` +
  `total 10 digits. A 3-digit area code therefore leaves a 7-digit subscriber ` +
  `number. Examples include Córdoba (351), Mendoza (261), Rosario (341), and ` +
  `Mar del Plata (223), with a landline format such as +54 351 123 4567. ` +
  `This quiz groups 4-digit area codes by their first three digits while ` +
  `complete 2- and 3-digit codes remain unchanged.`;

export const argentinaPhoneCodes3DigitQuiz: FeatureQuiz = {
  id: "argentina-phone-codes-3-digit",
  name: "3-Digit Phone Codes",
  description: ARGENTINA_PHONE_CODES_3_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "argentina-phone-codes-3-digit",

  answerProperty: "area_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "phone_code_1_digit",
        label: "1-Digit Prefix",
        valueType: "string",
      },
      {
        property: "phone_code_2_digit",
        label: "2-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: ARGENTINA_PHONE_CODES_3_DIGIT_QUESTIONS,
};
