import type { FeatureQuiz } from "@/types/quiz";

/**
 * All geographically useful first-digit telephone prefixes represented by
 * Panama's processed 1-digit phone-code GeoJSON.
 */
const PANAMA_PHONE_CODES_1_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "2" },
    { answer: "3" },
    { answer: "4" },
    { answer: "7" },
    { answer: "9" },
  ];

/**
 * User-facing description derived from the question array so it remains
 * accurate if the useful first-digit prefix set changes later.
 */
const PANAMA_PHONE_CODES_1_DIGIT_DESCRIPTION =
  `Learn ${PANAMA_PHONE_CODES_1_DIGIT_QUESTIONS.length} geographically useful first-digit phone prefixes in Panama. ` +
  `Useful regional clues come from 7-digit local numbers written like XXX-XXXX, where the first digit acts as the geographic prefix rather than a separate area-code addition. ` +
  `For example, a number beginning with 9 (9XX-XXXX) can provide a regional clue, while numbers beginning with 5, 6, or 8 are not useful for this quiz.`;

/**
 * Quiz definition for identifying Panama's geographically useful first-digit
 * telephone prefixes.
 *
 * Each GeoJSON feature stores its valid prefixes in the `codes` string-array
 * property. Some geographic features accept multiple prefixes, and a prefix
 * may correspond to multiple geographic features. For example, code 3 matches
 * both the dedicated `["3"]` region and the shared `["2", "3"]` region.
 */
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
