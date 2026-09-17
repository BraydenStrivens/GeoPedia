/**
 * Quiz configuration for Brazil's 1-digit telephone area-code groups.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { BRAZIL_PHONE_CODE_1_DIGIT_QUESTIONS } from "./data/phoneCodes";

const BRAZIL_PHONE_CODES_1_DIGIT_DESCRIPTION =
  `Learn the ${BRAZIL_PHONE_CODE_1_DIGIT_QUESTIONS.length} first-digit ` +
  `regions of Brazil's geographic telephone area codes. Brazilian area codes ` +
  `contain two digits and commonly appear before the local number as (XX) or ` +
  `XX followed by a space. The remaining telephone number contains 8 or 9 digits.`;

export const brazilPhoneCodes1DigitQuiz: FeatureQuiz = {
  id: "brazil-phone-codes-1-digit",
  name: "1-Digit Area Codes",
  description: BRAZIL_PHONE_CODES_1_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-phone-codes-1-digit",

  answerProperty: "phone_code",
  answerType: "single",

  questions: BRAZIL_PHONE_CODE_1_DIGIT_QUESTIONS,
};
