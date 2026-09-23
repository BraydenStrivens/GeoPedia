/**
 * Feature quiz for Ghana's first-level administrative regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { GHANA_REGIONS_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuiz["questions"] = Object.entries(
  GHANA_REGIONS_BY_ID,
).map(([regionId, region]) => ({
  answer: regionId,
  display: region.name,
}));

const DESCRIPTION = `Learn all ${QUESTIONS.length} first-level administrative regions of Ghana.`;

export const ghanaRegionsQuiz: FeatureQuiz = {
  id: "ghana-regions",
  name: "Regions",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "ghana-regions",

  answerProperty: "region_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: QUESTIONS,
};
