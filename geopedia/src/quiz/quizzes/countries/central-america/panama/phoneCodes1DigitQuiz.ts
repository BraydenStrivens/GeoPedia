/**
 * Quiz for identifying Panama's 1-digit phone-code regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PANAMA_PHONE_CODES_1_DIGIT_QUESTIONS } from "./data/phoneCodes";

const PANAMA_PHONE_CODES_1_DIGIT_DESCRIPTION =
  `Learn ${PANAMA_PHONE_CODES_1_DIGIT_QUESTIONS.length} geographically useful first-digit phone prefixes in Panama. ` +
  `Useful regional clues come from 7-digit local numbers written like XXX-XXXX, where the first digit acts as the geographic prefix rather than a separate area-code addition. ` +
  `For example, a number beginning with 9 (9XX-XXXX) can provide a regional clue, while numbers beginning with 5, 6, or 8 are not useful for this quiz.`;

export const panamaPhoneCodes1DigitQuiz: FeatureQuiz = {
  id: "panama-phone-codes-1-digit",
  name: "1-Digit Phone Codes",
  description: PANAMA_PHONE_CODES_1_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "panama-phone-codes-1-digit",

  answerProperty: "codes",
  answerType: "multiple",

  questions: PANAMA_PHONE_CODES_1_DIGIT_QUESTIONS,
};
