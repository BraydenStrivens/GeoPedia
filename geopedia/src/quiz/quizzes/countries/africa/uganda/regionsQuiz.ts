/**
 * Feature quiz for Uganda's four regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { UGANDA_REGIONS_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn all ${UGANDA_REGIONS_QUIZ_QUESTIONS.length} regions of Uganda.`;

export const ugandaRegionsQuiz: FeatureQuiz = {
  id: "uganda-regions",
  name: "Regions",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "uganda-regions",

  answerProperty: "region_id",
  answerType: "single",

  questions: UGANDA_REGIONS_QUIZ_QUESTIONS,
};
