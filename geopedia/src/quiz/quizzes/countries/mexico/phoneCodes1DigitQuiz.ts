import type { FeatureQuiz } from "@/types/quiz";

const MEXICO_PHONE_CODE_1_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "2", display: "2--" },
    { answer: "3", display: "3--" },
    { answer: "4", display: "4--" },
    { answer: "5", display: "5--" },
    { answer: "6", display: "6--" },
    { answer: "7", display: "7--" },
    { answer: "8", display: "8--" },
    { answer: "9", display: "9--" },
  ];

const MEXICO_PHONE_CODES_1_DIGIT_DESCRIPTION =
  `Learn all ${MEXICO_PHONE_CODE_1_DIGIT_QUESTIONS.length} 1-digit Mexican ` +
  `phone-code regions, representing the first digit of the full 2- or 3-digit ` +
  `area code. Mexican phone numbers contain 10 digits: 2-digit area codes are ` +
  `followed by an 8-digit local number, while 3-digit area codes are followed ` +
  `by a 7-digit local number.`;

/**
 * Quiz definition for identifying Mexico's 1-digit telephone-code regions.
 */
export const mexicoPhoneCodes1DigitQuiz: FeatureQuiz = {
  id: "mexico-phone-codes-1-digit",
  name: "Phone Codes 1-Digit",
  description: MEXICO_PHONE_CODES_1_DIGIT_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-phone-codes-1-digit",

  answerProperty: "prefix",
  answerType: "single",

  questions: MEXICO_PHONE_CODE_1_DIGIT_QUESTIONS,
};
