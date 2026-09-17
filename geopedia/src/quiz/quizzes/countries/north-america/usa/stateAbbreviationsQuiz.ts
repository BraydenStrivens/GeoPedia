/**
 * Quiz for identifying United States state abbreviations.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { US_STATE_ABBREVIATIONS } from "./data/stateAbbreviations";

const US_STATE_ABBREVIATION_QUESTIONS: FeatureQuiz["questions"] =
  US_STATE_ABBREVIATIONS.map((answer) => ({
    answer,
  }));

const US_STATE_ABBREVIATION_DESCRIPTION =
  `Learn the abbreviations for all ${US_STATE_ABBREVIATION_QUESTIONS.length} ` +
  `U.S. states. This quiz includes the 50 states only and does not include ` +
  `U.S. territories.`;

export const usStateAbbreviationsQuiz: FeatureQuiz = {
  id: "us-state-abbreviations",
  name: "State Abbreviations",
  description: US_STATE_ABBREVIATION_DESCRIPTION,

  mapId: "us-states",
  kind: "feature",

  answerProperty: "abbreviation",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: US_STATE_ABBREVIATION_QUESTIONS,
};
