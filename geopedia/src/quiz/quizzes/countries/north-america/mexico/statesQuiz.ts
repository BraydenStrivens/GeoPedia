/**
 * Quiz configuration for Mexico's states and federal entity.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { MEXICO_STATES_BY_ID } from "./data/admin";

const MEXICO_STATE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(MEXICO_STATES_BY_ID).map(([stateId, state]) => ({
    answer: stateId,
    display: state,
  }));

const MEXICO_STATES_DESCRIPTION =
  `Learn all ${MEXICO_STATE_QUESTIONS.length} states and federal entities ` +
  `of Mexico.`;

export const mexicoStatesQuiz: FeatureQuiz = {
  id: "mexico-states",
  name: "States",
  description: MEXICO_STATES_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-states",

  answerProperty: "state_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: MEXICO_STATE_QUESTIONS,
};
