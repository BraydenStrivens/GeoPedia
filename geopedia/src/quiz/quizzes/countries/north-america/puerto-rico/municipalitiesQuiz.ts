/**
 * Quiz for identifying Puerto Rico's municipalities.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { PUERTO_RICO_MUNICIPALITIES_BY_ID } from "./data/admin";

const PUERTO_RICO_MUNICIPALITY_QUESTIONS = Object.entries(
  PUERTO_RICO_MUNICIPALITIES_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

export const puertoRicoMunicipalitiesQuiz: FeatureQuiz = {
  id: "puerto-rico-municipalities",
  name: "Municipalities",
  description: `Learn all ${PUERTO_RICO_MUNICIPALITY_QUESTIONS.length} municipalities of Puerto Rico.`,

  kind: "feature",

  mapId: "puerto-rico-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: PUERTO_RICO_MUNICIPALITY_QUESTIONS,
};
