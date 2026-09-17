/**
 * Quiz for identifying United States telephone area codes.
 *
 * Each area code is presented as an independent answer. Geographic regions
 * containing overlay codes can therefore correspond to multiple answers.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { US_SUBDIVISION_BY_ABBREVIATION } from "./data/admin";
import { US_AREA_CODE_QUESTIONS } from "./data/areaCodes";

const US_AREA_CODE_DESCRIPTION =
  `Learn all ${US_AREA_CODE_QUESTIONS.length} U.S. area codes, including U.S. ` +
  `territories, with filtering options to practice any desired subset. U.S. ` +
  `phone numbers contain a 3-digit area code followed by a 7-digit local ` +
  `number, commonly formatted as (XXX) XXX-XXXX. Mobile and landline numbers ` +
  `use the same area-code system.`;

export const usAreaCodesQuiz: FeatureQuiz = {
  id: "us-area-codes",
  name: "Area Codes",
  description: US_AREA_CODE_DESCRIPTION,

  mapId: "us-area-codes",
  kind: "feature",

  answerProperty: "area_codes",
  answerType: "multiple",

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

  questions: US_AREA_CODE_QUESTIONS,
};
