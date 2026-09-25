/**
 * Quiz configuration for South Africa's geographic telephone area codes.
 *
 * South Africa has 36 geographic features represented in this dataset but
 * 37 quiz questions because 010 and 011 share the Johannesburg geographic
 * feature.
 *
 * The quiz therefore uses multiple-answer behavior so multiple questions can
 * resolve to the same geographic feature.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_AREA_CODE_QUESTIONS } from "./data/areaCodes";

const SOUTH_AFRICA_AREA_CODES_DESCRIPTION = `
Learn South Africa's geographic telephone area codes.
The quiz includes 37 area codes across 36 geographic regions. The 010 and 011
codes share the Johannesburg geographic region.`;

export const southAfricaAreaCodesQuiz: FeatureQuiz = {
  id: "south-africa-area-codes",
  name: "South Africa Area Codes",
  description: SOUTH_AFRICA_AREA_CODES_DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-area-codes",

  answerProperty: "area_codes",
  answerType: "multiple",

  grouping: {
    properties: [
      {
        property: "prefix_1",
        label: "1-Digit Prefix",
        valueType: "string",
      },
    ],
  },

  questions: SOUTH_AFRICA_AREA_CODE_QUESTIONS,
};
