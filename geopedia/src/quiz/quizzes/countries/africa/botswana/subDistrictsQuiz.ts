/**
 * Feature quiz configuration for Botswana's sub-districts.
 *
 * Sub-districts can be grouped by their associated district. The source
 * hierarchy uses Botswana's rural districts, with Gaborone retained as its
 * own grouping value.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { BOTSWANA_SUB_DISTRICTS_QUIZ_QUESTIONS } from "./data/admin";

const BOTSWANA_SUB_DISTRICTS_DESCRIPTION =
  `Learn all ${BOTSWANA_SUB_DISTRICTS_QUIZ_QUESTIONS.length} sub-districts ` +
  "of Botswana.";

export const botswanaSubDistrictsQuiz: FeatureQuiz = {
  id: "botswana-sub-districts",
  name: "Sub-districts",
  description: BOTSWANA_SUB_DISTRICTS_DESCRIPTION,

  kind: "feature",
  mapId: "botswana-sub-districts",

  answerProperty: "sub_district_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
  },

  grouping: {
    properties: [
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
    ],
  },

  questions: BOTSWANA_SUB_DISTRICTS_QUIZ_QUESTIONS,
};
