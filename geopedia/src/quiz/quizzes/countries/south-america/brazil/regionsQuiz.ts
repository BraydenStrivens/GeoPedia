/**
 * Quiz configuration for Brazil's five geographic regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { BRAZIL_REGIONS_BY_ID } from "./data/admin";

const BRAZIL_REGION_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BRAZIL_REGIONS_BY_ID).map(([regionId, region]) => ({
    answer: regionId,
    display: region,
  }));

const BRAZIL_REGIONS_DESCRIPTION =
  `Learn all ${BRAZIL_REGION_QUESTIONS.length} official geographic regions ` +
  `of Brazil.`;

export const brazilRegionsQuiz: FeatureQuiz = {
  id: "brazil-regions",
  name: "Regions",
  description: BRAZIL_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-regions",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: BRAZIL_REGION_QUESTIONS,
};
