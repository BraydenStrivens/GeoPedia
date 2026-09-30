/**
 * Quiz configuration for Malaysia's states and federal territories.
 */

import { FeatureQuiz } from "@/types/quiz";

import { MALAYSIA_STATE_QUESTIONS } from "./data/admin";

const MALAYSIA_STATES_DESCRIPTION = `Learn all ${MALAYSIA_STATE_QUESTIONS.length} states and federal territories of Malaysia.`;

export const malaysiaStatesQuiz: FeatureQuiz = {
  id: "malaysia-states",
  name: "Negeri & Wilayah Persekutuan (States & Federal Territories)",
  description: MALAYSIA_STATES_DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "malaysia-states",

  answerProperty: "state_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: MALAYSIA_STATE_QUESTIONS,
};
