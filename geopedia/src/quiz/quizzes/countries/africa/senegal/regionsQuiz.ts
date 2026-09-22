/**
 * Defines Senegal's first-level administrative region quiz.
 *
 * Base-map subdivision labels are hidden so they do not reveal region answers.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SENEGAL_REGIONS_BY_ID } from "./data/admin";

const SENEGAL_REGION_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(SENEGAL_REGIONS_BY_ID).map(([regionId, region]) => ({
    answer: regionId,
    display: region,
  }));

const SENEGAL_REGIONS_DESCRIPTION =
  `Learn all ${SENEGAL_REGION_QUESTIONS.length} first-level administrative ` +
  `regions of Senegal.`;

export const senegalRegionsQuiz: FeatureQuiz = {
  id: "senegal-regions",
  name: "Regions",
  description: SENEGAL_REGIONS_DESCRIPTION,

  kind: "feature",
  mapId: "senegal-regions",

  answerProperty: "region_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
    subdivisionBorders: false,
  },

  questions: SENEGAL_REGION_QUESTIONS,
};
