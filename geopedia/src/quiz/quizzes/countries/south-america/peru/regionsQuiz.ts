/**
 * Quiz configuration for Peru's first-level administrative regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PERU_REGIONS_BY_ID } from "./data/admin";

const PERU_REGION_QUESTIONS = Object.entries(PERU_REGIONS_BY_ID).map(
  ([regionId, region]) => ({
    answer: regionId,
    display: region,
  }),
);

const PERU_REGIONS_DESCRIPTION =
  `Learn all ${PERU_REGION_QUESTIONS.length} first-level administrative ` +
  `regions of Peru, including the Constitutional Province of Callao.`;

export const peruRegionsQuiz: FeatureQuiz = {
  id: "peru-regions",
  name: "Regions",
  description: PERU_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "peru-regions",

  answerProperty: "region_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PERU_REGION_QUESTIONS,
};
