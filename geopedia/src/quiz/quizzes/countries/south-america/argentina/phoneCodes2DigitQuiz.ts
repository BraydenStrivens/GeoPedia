/**
 * Quiz configuration for Argentina's two-digit geographic telephone-code
 * regions.
 *
 * Longer area codes are grouped by their first two digits, while complete
 * two-digit area codes remain unchanged.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ARGENTINA_PHONE_CODES_2_DIGIT } from "./data/phoneCodes";

const ARGENTINA_PHONE_CODES_2_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  ARGENTINA_PHONE_CODES_2_DIGIT.map((areaCode) => ({
    answer: areaCode,
  }));

const ARGENTINA_PHONE_CODES_2_DIGIT_DESCRIPTION =
  `Learn all ${ARGENTINA_PHONE_CODES_2_DIGIT_QUESTIONS.length} two-digit ` +
  `telephone-code regions of Argentina. Argentine geographic telephone numbers ` +
  `include the area code plus subscriber number, which always ` +
  `totals 10 digits. Area codes can be 2, 3, or 4 digits long. For example, ` +
  `Buenos Aires uses the complete 2-digit area code 11, giving a landline ` +
  `format such as +54 11 4123 4567. This quiz groups longer area codes by ` +
  `their first two digits while complete 2-digit codes remain unchanged.`;

export const argentinaPhoneCodes2DigitQuiz: FeatureQuiz = {
  id: "argentina-phone-codes-2-digit",
  name: "2-Digit Phone Codes",
  description: ARGENTINA_PHONE_CODES_2_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "argentina-phone-codes-2-digit",

  answerProperty: "area_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "phone_code_1_digit",
        label: "1-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: ARGENTINA_PHONE_CODES_2_DIGIT_QUESTIONS,
};
