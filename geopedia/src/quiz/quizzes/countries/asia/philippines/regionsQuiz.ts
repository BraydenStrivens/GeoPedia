/**
 * Feature quiz for the Philippines' 17 regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PHILIPPINES_REGION_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${PHILIPPINES_REGION_QUESTIONS.length} regions ` +
  `of the Philippines.`;

export const philippinesRegionsQuiz: FeatureQuiz = {
  id: "philippines-regions",
  name: "Regions",
  description: DESCRIPTION,

  kind: "feature",
  quizTopic: "Administrative Regions",
  mapId: "philippines-regions",

  answerProperty: "region_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PHILIPPINES_REGION_QUESTIONS,
};
