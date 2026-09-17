/**
 * Quiz configuration for Brazil's 2-digit telephone area codes.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { BRAZIL_PHONE_CODE_2_DIGIT_QUESTIONS } from "./data/phoneCodes";

const BRAZIL_PHONE_CODES_2_DIGIT_DESCRIPTION =
  `Learn all ${BRAZIL_PHONE_CODE_2_DIGIT_QUESTIONS.length} two-digit ` +
  `geographic telephone area codes used across Brazil. Area codes commonly ` +
  `appear before the local number as (XX) or XX followed by a space. The ` +
  `remaining telephone number contains 8 or 9 digits.`;

export const brazilPhoneCodes2DigitQuiz: FeatureQuiz = {
  id: "brazil-phone-codes-2-digit",
  name: "2-Digit Area Codes",
  description: BRAZIL_PHONE_CODES_2_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-phone-codes-2-digit",

  answerProperty: "phone_code",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "phone_code_1_digit",
        label: "First Digit",
        valueType: "string",
      },
    ],
  },

  questions: BRAZIL_PHONE_CODE_2_DIGIT_QUESTIONS,
};
