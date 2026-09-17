/**
 * Quiz for identifying the Dominican Republic's provinces and
 * province-equivalent divisions.
 *
 * Provinces can be grouped by their parent administrative region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  DOMINICAN_REPUBLIC_PROVINCES_BY_ID,
  DOMINICAN_REPUBLIC_REGIONS_BY_ID,
} from "./data/admin";

const DOMINICAN_REPUBLIC_PROVINCE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(DOMINICAN_REPUBLIC_PROVINCES_BY_ID).map(
    ([answer, province]) => ({
      answer,
      display: province.name,
    }),
  );

const DOMINICAN_REPUBLIC_PROVINCES_DESCRIPTION =
  `Learn all ${DOMINICAN_REPUBLIC_PROVINCE_QUESTIONS.length} provinces and ` +
  `province-equivalent regions of the Dominican Republic, with filters that ` +
  `let you practice any desired region or combination of regions.`;

export const dominicanRepublicProvincesQuiz: FeatureQuiz = {
  id: "dominican-republic-provinces",
  name: "Dominican Republic Provinces",
  description: DOMINICAN_REPUBLIC_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "dominican-republic-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: DOMINICAN_REPUBLIC_REGIONS_BY_ID,
      },
    ],
  },

  questions: DOMINICAN_REPUBLIC_PROVINCE_QUESTIONS,
};
