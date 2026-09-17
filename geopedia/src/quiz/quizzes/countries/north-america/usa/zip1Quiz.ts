/**
 * Quiz for identifying United States 1-digit ZIP-code prefixes.
 *
 * Prefixes are displayed as the beginning of a five-digit ZIP code,
 * with the remaining positions represented by hyphens.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { US_ZIP_1_DIGIT_QUESTIONS } from "./data/zipCodes";

const US_ZIP_1_DESCRIPTION =
  `Learn all ${US_ZIP_1_DIGIT_QUESTIONS.length} U.S. 1-digit ZIP code regions, ` +
  `representing the first digit of an otherwise 5-digit ZIP code. This quiz ` +
  `includes U.S. territories and provides filtering options to practice any ` +
  `desired subset.`;

export const usZip1Quiz: FeatureQuiz = {
  id: "us-zip-1",
  name: "1-Digit ZIP Codes",
  description: US_ZIP_1_DESCRIPTION,

  mapId: "us-zip-1",
  kind: "feature",

  answerProperty: "zip",
  answerType: "single",

  questions: US_ZIP_1_DIGIT_QUESTIONS,
};
