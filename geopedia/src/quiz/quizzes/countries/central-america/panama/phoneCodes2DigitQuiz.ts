/**
 * Quiz for identifying Panama's 2-digit phone-code regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PANAMA_PHONE_CODES_2_DIGIT_QUESTIONS } from "./data/phoneCodes";

const PANAMA_PHONE_CODES_2_DIGIT_DESCRIPTION =
  `Learn ${PANAMA_PHONE_CODES_2_DIGIT_QUESTIONS.length} geographically useful regional phone prefixes in Panama. ` +
  `Useful clues come from the beginning of 7-digit local numbers written like XXX-XXXX. ` +
  `This quiz uses the more precise 2-digit regional prefix where available, while regions without a more specific prefix retain their useful 1-digit code. ` +
  `Numbers beginning with 5, 6, or 8 are not useful for this regional clue.`;

export const panamaPhoneCodes2DigitQuiz: FeatureQuiz = {
  id: "panama-phone-codes-2-digit",
  name: "2-Digit Phone Codes",
  description: PANAMA_PHONE_CODES_2_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "panama-phone-codes-2-digit",

  answerProperty: "codes",
  answerType: "multiple",

  questions: PANAMA_PHONE_CODES_2_DIGIT_QUESTIONS,
};
