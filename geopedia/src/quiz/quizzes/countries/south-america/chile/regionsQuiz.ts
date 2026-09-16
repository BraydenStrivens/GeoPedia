/**
 * Defines Chile's first-level administrative region quiz.
 *
 * Base-map subdivision labels are hidden so they do not reveal region answers.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CHILE_REGIONS_BY_ID } from "./data/admin";

const CHILE_REGION_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(CHILE_REGIONS_BY_ID).map(([regionId, region]) => ({
    answer: regionId,
    display: region,
  }));

const CHILE_REGIONS_DESCRIPTION =
  `Learn all ${CHILE_REGION_QUESTIONS.length} first-level administrative ` +
  `regions of Chile.`;

export const chileRegionsQuiz: FeatureQuiz = {
  id: "chile-regions",
  name: "Regions",
  description: CHILE_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "chile-regions",

  answerProperty: "region_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: CHILE_REGION_QUESTIONS,
};
