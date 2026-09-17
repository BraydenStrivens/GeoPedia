/**
 * Quiz for identifying United States 3-digit ZIP-code prefixes.
 *
 * Prefixes are displayed as the beginning of a five-digit ZIP code,
 * with the remaining positions represented by hyphens.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { US_SUBDIVISION_BY_ABBREVIATION } from "./data/admin";
import { US_ZIP_3_DIGIT_QUESTIONS } from "./data/zipCodes";

const US_ZIP_3_DESCRIPTION =
  `Learn all ${US_ZIP_3_DIGIT_QUESTIONS.length} U.S. 3-digit ZIP code regions, ` +
  `representing the first three digits of an otherwise 5-digit ZIP code. This ` +
  `quiz includes U.S. territories and provides filtering options to practice ` +
  `any desired subset.`;

export const usZip3Quiz: FeatureQuiz = {
  id: "us-zip-3",
  name: "3-Digit ZIP Codes",
  description: US_ZIP_3_DESCRIPTION,

  mapId: "us-zip-3",
  kind: "feature",

  answerProperty: "zip",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "states",
        label: "State",
        valueType: "string-array",
        valueLabels: US_SUBDIVISION_BY_ABBREVIATION,
      },
    ],
  },

  questions: US_ZIP_3_DIGIT_QUESTIONS,
};
