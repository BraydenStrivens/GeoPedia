/**
 * Quiz configuration for Brazil's states and Federal District.
 *
 * Questions can be grouped by region for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  BRAZIL_REGIONS_BY_ID,
  BRAZIL_STATES_BY_ID,
} from "./data/admin";

const BRAZIL_STATE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BRAZIL_STATES_BY_ID).map(([stateId, state]) => ({
    answer: stateId,
    display: state.name,
  }));

const BRAZIL_STATES_DESCRIPTION =
  `Learn all ${BRAZIL_STATE_QUESTIONS.length} state-level divisions of Brazil, ` +
  `including the Federal District.`;

export const brazilStatesQuiz: FeatureQuiz = {
  id: "brazil-states",
  name: "States",
  description: BRAZIL_STATES_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-states",

  answerProperty: "id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: BRAZIL_REGIONS_BY_ID,
      },
    ],
  },

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: BRAZIL_STATE_QUESTIONS,
};
