/**
 * Quiz for identifying Panama's provinces and indigenous comarcas.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PANAMA_PROVINCES_COMARCAS_BY_ID } from "./data/admin";

const PANAMA_PROVINCE_COMARCA_QUESTIONS = Object.entries(
  PANAMA_PROVINCES_COMARCAS_BY_ID,
).map(([id, name]) => ({
  answer: id,
  display: name,
}));

export const panamaProvincesComarcasQuiz: FeatureQuiz = {
  id: "panama-provinces-comarcas",
  name: "Provinces & Comarcas",
  description: `Learn all ${PANAMA_PROVINCE_COMARCA_QUESTIONS.length} provinces and province-level comarcas of Panama.`,

  kind: "feature",
  mapId: "panama-provinces-comarcas",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PANAMA_PROVINCE_COMARCA_QUESTIONS,
};
