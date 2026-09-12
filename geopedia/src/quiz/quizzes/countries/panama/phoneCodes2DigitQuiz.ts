import type { FeatureQuiz } from "@/types/quiz";

/**
 * All geographically useful regional telephone prefixes represented by
 * Panama's processed 2-digit phone-code GeoJSON.
 *
 * Some regions retain a broader 1-digit prefix where Plonk It does not
 * provide a more precise 2-digit regional prefix.
 */
const PANAMA_PHONE_CODES_2_DIGIT_QUESTIONS: FeatureQuiz["questions"] =
  [
    { answer: "2" },
    { answer: "3" },
    { answer: "4" },
    { answer: "7" },
    { answer: "24" },
    { answer: "25" },
    { answer: "29" },
    { answer: "34" },
    { answer: "75" },
    { answer: "90" },
    { answer: "93" },
    { answer: "95" },
    { answer: "96" },
    { answer: "97" },
    { answer: "98" },
  ];

/**
 * User-facing description derived from the question array so it remains
 * accurate if the useful regional prefix set changes later.
 */
const PANAMA_PHONE_CODES_2_DIGIT_DESCRIPTION =
  `Learn ${PANAMA_PHONE_CODES_2_DIGIT_QUESTIONS.length} geographically useful regional phone prefixes in Panama. ` +
  `Useful clues come from the beginning of 7-digit local numbers written like XXX-XXXX. ` +
  `This quiz uses the more precise 2-digit regional prefix where available, while regions without a more specific prefix retain their useful 1-digit code. ` +
  `Numbers beginning with 5, 6, or 8 are not useful for this regional clue.`;

/**
 * Quiz definition for identifying Panama's more precise regional telephone
 * prefixes.
 *
 * Each GeoJSON feature stores its valid prefixes in the `codes` string-array
 * property. A geographic feature may accept multiple prefixes, and a prefix
 * may correspond to multiple geographic features.
 */
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
