/**
 * Feature quiz configuration for Botswana's districts.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { BOTSWANA_DISTRICTS_QUIZ_QUESTIONS } from "./data/admin";

const BOTSWANA_DISTRICTS_DESCRIPTION = `Learn all ${BOTSWANA_DISTRICTS_QUIZ_QUESTIONS.length} districts of Botswana.`;

export const botswanaDistrictsQuiz: FeatureQuiz = {
  id: "botswana-districts",
  name: "Districts",
  description: BOTSWANA_DISTRICTS_DESCRIPTION,

  kind: "feature",
  mapId: "botswana-districts",

  answerProperty: "district_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
    subdivisionLabels: false,
  },

  questions: BOTSWANA_DISTRICTS_QUIZ_QUESTIONS,
};
