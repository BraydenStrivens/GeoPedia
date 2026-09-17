/**
 * Quiz for identifying United States states and other included subdivisions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { US_SUBDIVISION_BY_ABBREVIATION } from "./data/admin";
import { US_STATE_ABBREVIATIONS } from "./data/stateAbbreviations";

const US_STATE_QUESTIONS: FeatureQuiz["questions"] =
  US_STATE_ABBREVIATIONS.map((abbreviation) => ({
    answer: US_SUBDIVISION_BY_ABBREVIATION[abbreviation],
  }));

const US_STATES_DESCRIPTION =
  `Learn all ${US_STATE_QUESTIONS.length} U.S. states by their location on the ` +
  `map. This quiz includes the 50 states only and does not include U.S. ` +
  `territories.`;

export const usStatesQuiz: FeatureQuiz = {
  id: "us-states",
  name: "States",
  description: US_STATES_DESCRIPTION,

  kind: "feature",
  mapId: "us-states",

  answerProperty: "name",
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

  questions: US_STATE_QUESTIONS,
};
