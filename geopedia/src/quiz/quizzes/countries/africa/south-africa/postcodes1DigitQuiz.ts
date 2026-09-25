/**
 * South Africa one-digit postcode-prefix feature quiz.
 *
 * This is the broadest postcode quiz, grouping the reconstructed postcode
 * geography into the ten first-digit postal regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_POSTCODES_1_QUIZ_QUESTIONS } from "./data/postcodes";

const DESCRIPTION =
  `Learn the 1-digit postal code prefixes of South Africa.\n\n` +
  `South African postal codes contain four digits, and their first digit ` +
  `identifies a broad postal region. For example, 1281 in Ximhungwe begins ` +
  `with 1 and 5850 in Somerset East begins with 5`;

export const southAfricaPostcodes1DigitQuiz: FeatureQuiz = {
  id: "south-africa-postcodes-1",
  name: "1-Digit Postcode Prefixes",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-postcodes-1",

  answerProperty: "prefix_1",
  answerType: "single",

  questions: SOUTH_AFRICA_POSTCODES_1_QUIZ_QUESTIONS,
};
