/**
 * Quiz for identifying Costa Rica's provinces.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COSTA_RICA_PROVINCES_BY_ID } from "./data/admin";

const COSTA_RICA_PROVINCE_QUESTIONS = Object.entries(
  COSTA_RICA_PROVINCES_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

export const costaRicaProvincesQuiz: FeatureQuiz = {
  id: "costa-rica-provinces",
  name: "Provinces",
  description: `Learn all ${COSTA_RICA_PROVINCE_QUESTIONS.length} provinces of Costa Rica.`,

  kind: "feature",
  mapId: "costa-rica-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: COSTA_RICA_PROVINCE_QUESTIONS,
};
