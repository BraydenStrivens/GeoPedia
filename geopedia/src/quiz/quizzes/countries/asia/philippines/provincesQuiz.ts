/**
 * Feature quiz for the Philippines' provinces and province-level units.
 *
 * Provinces and province-level units can be grouped by region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PHILIPPINES_PROVINCE_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${PHILIPPINES_PROVINCE_QUESTIONS.length} ` +
  `provinces and province-level units of the Philippines.\n\n` +
  `Group the quiz by region to focus on one part of the country at a time.`;

export const philippinesProvincesQuiz: FeatureQuiz = {
  id: "philippines-provinces",
  name: "Provinces",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "philippines-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: PHILIPPINES_PROVINCE_QUESTIONS,
};
