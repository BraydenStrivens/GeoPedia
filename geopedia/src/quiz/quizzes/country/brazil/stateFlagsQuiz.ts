import type { FeatureQuiz } from "@/types/quiz";

import { BRAZIL_REGION_NAMES_BY_ID } from "./regionsQuiz";
import { BRAZIL_STATE_ABBREVIATIONS_BY_ID } from "./stateAbbreviationsQuiz";
import { BRAZIL_STATE_NAMES_BY_ID } from "./statesQuiz";
/**
 * Questions for Brazil's State Flags quiz.
 *
 * State names are used for the quiz answers and display text, while state
 * abbreviations are used only to resolve the corresponding flag SVG files.
 */
const BRAZIL_STATE_FLAG_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BRAZIL_STATE_NAMES_BY_ID).map(
    ([answer, display]) => {
      const abbreviation =
        BRAZIL_STATE_ABBREVIATIONS_BY_ID[
          answer as keyof typeof BRAZIL_STATE_ABBREVIATIONS_BY_ID
        ];

      return {
        answer,
        display,
        prompt: {
          type: "image",
          imageUrl: `/data/countries/brazil/flags/${abbreviation.toLowerCase()}.svg`,
          alt: `${display} state flag`,
        },
      };
    },
  );

/**
 * Description shown for Brazil's State Flags quiz.
 */
const BRAZIL_STATE_FLAGS_DESCRIPTION =
  `Learn the flags of all ${BRAZIL_STATE_FLAG_QUESTIONS.length} state-level ` +
  `divisions of Brazil, including the Federal District.`;

/**
 * Quiz configuration for Brazil's state and Federal District flags.
 */
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
        valueLabels: BRAZIL_REGION_NAMES_BY_ID,
      },
    ],
  },

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: BRAZIL_STATE_FLAG_QUESTIONS,
};
