/**
 * Quiz configuration for identifying Mexico's states and federal entity
 * from their abbreviations.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { MEXICO_STATE_ABBREVIATIONS_BY_ID } from "./data/stateAbbreviations";

const MEXICO_STATE_ABBREVIATION_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(MEXICO_STATE_ABBREVIATIONS_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

const MEXICO_STATE_ABBREVIATIONS_DESCRIPTION =
  `Learn the conventional abbreviations for all ` +
  `${MEXICO_STATE_ABBREVIATION_QUESTIONS.length} Mexican federal entities.`;

export const mexicoStateAbbreviationsQuiz: FeatureQuiz = {
  id: "mexico-state-abbreviations",
  name: "State Abbreviations",
  description: MEXICO_STATE_ABBREVIATIONS_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-states",

  answerProperty: "state_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: MEXICO_STATE_ABBREVIATION_QUESTIONS,
};
