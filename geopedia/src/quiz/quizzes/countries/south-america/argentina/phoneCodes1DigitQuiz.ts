/**
 * Quiz configuration for Argentina's first-digit geographic telephone-code
 * regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ARGENTINA_PHONE_CODES_1_DIGIT } from "./data/phoneCodes";

const ARGENTINA_PHONE_CODES_1_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  ARGENTINA_PHONE_CODES_1_DIGIT.map((areaCode) => ({
    answer: areaCode,
  }));

const ARGENTINA_PHONE_CODES_1_DIGIT_DESCRIPTION =
  `Learn all ${ARGENTINA_PHONE_CODES_1_DIGIT_QUESTIONS.length} first-digit ` +
  `telephone-code regions of Argentina. Argentine geographic telephone numbers ` +
  `include the area code plus subscriber, and the number always ` +
  `totals 10 digits. Area codes are 2, 3, or 4 digits long, leaving 8, 7, or ` +
  `6 digits for the subscriber number. This introductory quiz groups area ` +
  `codes by their first digit before moving on to more detailed prefixes.`;

export const argentinaPhoneCodes1DigitQuiz: FeatureQuiz = {
  id: "argentina-phone-codes-1-digit",
  name: "1-Digit Phone Codes",
  description: ARGENTINA_PHONE_CODES_1_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "argentina-phone-codes-1-digit",

  answerProperty: "area_code",
  answerType: "single",

  questions: ARGENTINA_PHONE_CODES_1_DIGIT_QUESTIONS,
};
