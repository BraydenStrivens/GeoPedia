/**
 * Feature quiz for Rwanda's intara (provinces) and City of Kigali.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { RWANDA_PROVINCES_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${RWANDA_PROVINCES_QUIZ_QUESTIONS.length} intara (provinces) ` +
  `of Rwanda, including the City of Kigali.`;

export const rwandaProvincesQuiz: FeatureQuiz = {
  id: "rwanda-provinces",
  name: "Intara (Provinces)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "rwanda-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: RWANDA_PROVINCES_QUIZ_QUESTIONS,
};
