import { MEXICO_STATE_ABBREVIATIONS_BY_ID } from "@/constants/mexicoSubdivisions";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * Quiz questions generated from the state-abbreviation mapping.
 *
 * `answer` remains the stable INEGI state ID used by the shared Mexico states
 * map, while `display` is the abbreviation shown to the player.
 */
const MEXICO_STATE_ABBREVIATION_QUESTIONS = Object.entries(
  MEXICO_STATE_ABBREVIATIONS_BY_ID,
).map(([stateId, abbreviation]) => ({
  answer: stateId,
  display: abbreviation,
}));

/**
 * Quiz for learning conventional abbreviations of Mexico's 32 federal
 * entities.
 *
 * This reuses the same processed INEGI state map as the full-name state quiz.
 * No abbreviation data needs to be stored in the GeoJSON because each quiz
 * question maps directly to the state's stable INEGI identifier.
 */
export const mexicoStateAbbreviationsQuiz: FeatureQuiz = {
  id: "mexico-state-abbreviations",
  name: "State Abbreviations",
  description: `Learn the abbreviations for all ${MEXICO_STATE_ABBREVIATION_QUESTIONS.length} Mexican federal entities.`,
  kind: "feature",

  mapId: "mexico-states",

  answerProperty: "state_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: MEXICO_STATE_ABBREVIATION_QUESTIONS,
};
