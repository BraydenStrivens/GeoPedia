/**
 * Feature quiz for Eswatini's regions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ESWATINI_REGION_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn the ${ESWATINI_REGION_QUIZ_QUESTIONS.length} regions of Eswatini.`;

export const eswatiniRegionsQuiz: FeatureQuiz = {
  id: "eswatini-regions",
  name: "Regions",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "eswatini-regions",

  answerProperty: "region_id",
  answerType: "single",

  questions: ESWATINI_REGION_QUIZ_QUESTIONS,
};
