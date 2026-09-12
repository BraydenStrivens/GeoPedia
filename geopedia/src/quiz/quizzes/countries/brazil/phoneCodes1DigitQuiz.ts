import type { FeatureQuiz } from "@/types/quiz";

/**
 * First digits of Brazil's two-digit geographic telephone area codes.
 */
const BRAZIL_PHONE_CODE_1_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "1", display: "1-" },
    { answer: "2", display: "2-" },
    { answer: "3", display: "3-" },
    { answer: "4", display: "4-" },
    { answer: "5", display: "5-" },
    { answer: "6", display: "6-" },
    { answer: "7", display: "7-" },
    { answer: "8", display: "8-" },
    { answer: "9", display: "9-" },
  ];

/**
 * Description shown for Brazil's 1-Digit Area Codes quiz.
 */
/**
 * Description shown for Brazil's 1-Digit Area Codes quiz.
 */
const BRAZIL_PHONE_CODES_1_DIGIT_DESCRIPTION =
  `Learn the ${BRAZIL_PHONE_CODE_1_DIGIT_QUESTIONS.length} first-digit ` +
  `regions of Brazil's geographic telephone area codes. Brazilian area codes ` +
  `contain two digits and commonly appear before the local number as (XX) or ` +
  `XX followed by a space. The remaining telephone number contains 8 or 9 digits.`;

/**
 * Quiz configuration for the first digit of Brazil's telephone area codes.
 */
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
