/**
 * Feature quiz for Lesotho's 10 districts.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { LESOTHO_DISTRICT_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn the ${LESOTHO_DISTRICT_QUIZ_QUESTIONS.length} districts of Lesotho.`;

export const lesothoDistrictsQuiz: FeatureQuiz = {
  id: "lesotho-districts",
  name: "Districts",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "lesotho-districts",

  answerProperty: "district_id",
  answerType: "single",

  questions: LESOTHO_DISTRICT_QUIZ_QUESTIONS,
};
