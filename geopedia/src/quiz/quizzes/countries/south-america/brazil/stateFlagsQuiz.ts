/**
 * Quiz configuration for identifying Brazil's states and Federal District
 * from their flags.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  BRAZIL_REGIONS_BY_ID,
  BRAZIL_STATES_BY_ID,
} from "./data/admin";
import { BRAZIL_STATE_ABBREVIATIONS_BY_ID } from "./data/stateAbbreviations";

const BRAZIL_STATE_FLAG_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BRAZIL_STATES_BY_ID).map(([answer, state]) => {
    const abbreviation =
      BRAZIL_STATE_ABBREVIATIONS_BY_ID[
        answer as keyof typeof BRAZIL_STATE_ABBREVIATIONS_BY_ID
      ];

    return {
      answer,
      display: state.name,
      prompt: {
        type: "image",
        imageUrl: `/data/countries/brazil/flags/${abbreviation.toLowerCase()}.svg`,
        alt: `${state.name} state flag`,
      },
    };
  });

const BRAZIL_STATE_FLAGS_DESCRIPTION =
  `Learn the flags of all ${BRAZIL_STATE_FLAG_QUESTIONS.length} state-level ` +
  `divisions of Brazil, including the Federal District.`;

export const brazilStateFlagsQuiz: FeatureQuiz = {
  id: "brazil-state-flags",
  name: "State Flags",
  description: BRAZIL_STATE_FLAGS_DESCRIPTION,

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

  questions: BRAZIL_STATE_FLAG_QUESTIONS,
};
