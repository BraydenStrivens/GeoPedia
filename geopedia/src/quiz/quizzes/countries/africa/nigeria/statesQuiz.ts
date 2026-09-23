/**
 * Feature quiz for Nigeria's states and Federal Capital Territory.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { NIGERIA_STATES_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuiz["questions"] = Object.entries(
  NIGERIA_STATES_BY_ID,
).map(([stateId, state]) => ({
  answer: stateId,
  display: state.name,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} states and the Federal Capital Territory ` +
  `of Nigeria.`;

export const nigeriaStatesQuiz: FeatureQuiz = {
  id: "nigeria-states",
  name: "States",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "nigeria-states",

  answerProperty: "state_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
    subdivisionBorders: false,
  },

  questions: QUESTIONS,
};
