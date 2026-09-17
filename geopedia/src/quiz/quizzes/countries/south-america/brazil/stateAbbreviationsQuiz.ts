/**
 * Quiz configuration for identifying Brazil's states and Federal District
 * from their official abbreviations.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { BRAZIL_REGIONS_BY_ID } from "./data/admin";
import { BRAZIL_STATE_ABBREVIATIONS_BY_ID } from "./data/stateAbbreviations";

/**
 * Questions for Brazil's State Abbreviations quiz.
 */
const BRAZIL_STATE_ABBREVIATION_QUESTIONS: FeatureQuiz["questions"] =
  Object.values(BRAZIL_STATE_ABBREVIATIONS_BY_ID).map((answer) => ({
    answer,
  }));

/**
 * Description shown for Brazil's State Abbreviations quiz.
 */
const BRAZIL_STATE_ABBREVIATIONS_DESCRIPTION =
  `Learn all ${BRAZIL_STATE_ABBREVIATION_QUESTIONS.length} two-letter ` +
  `abbreviations used for Brazil's states and Federal District.`;

/**
 * Quiz configuration for Brazil's state and Federal District abbreviations.
 */
export const brazilStateAbbreviationsQuiz: FeatureQuiz = {
  id: "brazil-state-abbreviations",
  name: "State Abbreviations",
  description: BRAZIL_STATE_ABBREVIATIONS_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-states",

  answerProperty: "abbreviation",
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

  questions: BRAZIL_STATE_ABBREVIATION_QUESTIONS,
};
