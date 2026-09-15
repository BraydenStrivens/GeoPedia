import type { FeatureQuiz } from "@/types/quiz";

import { ARGENTINA_PHONE_CODES_FULL } from "./data/phoneCodes";

const ARGENTINA_PHONE_CODES_4_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  ARGENTINA_PHONE_CODES_FULL.map((areaCode) => ({
    answer: areaCode,
    display: areaCode,
  }));

const ARGENTINA_PHONE_CODES_4_DIGIT_DESCRIPTION =
  `Learn all ${ARGENTINA_PHONE_CODES_4_DIGIT_QUESTIONS.length} complete ` +
  `geographic telephone area codes of Argentina. Argentine geographic telephone ` +
  `include the area code plus subscriber number, these ` +
  `always total 10 digits. Area codes can contain 2, 3, or 4 digits, leaving ` +
  `8, 7, or 6 digits for the subscriber number. Examples include Buenos Aires ` +
  `(11), Córdoba (351), Bariloche (2944), and Ushuaia (2901). A 4-digit code ` +
  `produces a landline format such as +54 2944 12 3456. For international ` +
  `mobile numbers, 9 is inserted after +54, such as +54 9 2944 12 3456. ` +
  `This maximum-detail quiz uses each area's complete code rather than a ` +
  `shortened prefix.`;

export const argentinaPhoneCodes4DigitQuiz: FeatureQuiz = {
  id: "argentina-phone-codes-4-digit",
  name: "4-Digit Phone Codes",
  description: ARGENTINA_PHONE_CODES_4_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "argentina-phone-codes-full",

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
      {
        property: "phone_code_3_digit",
        label: "3-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: ARGENTINA_PHONE_CODES_4_DIGIT_QUESTIONS,
};
