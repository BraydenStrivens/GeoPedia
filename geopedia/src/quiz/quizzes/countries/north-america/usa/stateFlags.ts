/**
 * Image quiz for identifying United States subdivision flags.
 *
 * Flag questions are derived from the shared subdivision
 * abbreviation-to-name dictionary.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { US_SUBDIVISION_BY_ABBREVIATION } from "./data/admin";
import { US_STATE_ABBREVIATIONS } from "./data/stateAbbreviations";

const US_STATE_FLAG_QUESTIONS: FeatureQuiz["questions"] =
  US_STATE_ABBREVIATIONS.map((abbreviation) => ({
    answer: US_SUBDIVISION_BY_ABBREVIATION[abbreviation],
    prompt: {
      type: "image",
      imageUrl: `/data/countries/usa/flags/${abbreviation.toLowerCase()}.svg`,
      alt: "State Flag",
    },
  }));

const US_STATE_FLAGS_DESCRIPTION =
  `Learn the flags of all ${US_STATE_FLAG_QUESTIONS.length} U.S. states by ` +
  `identifying each state on the map.`;

export const usStateFlagsQuiz: FeatureQuiz = {
  id: "us-state-flags",
  name: "State Flags",
  description: US_STATE_FLAGS_DESCRIPTION,

  kind: "feature",
  mapId: "us-states",

  answerProperty: "name",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: US_STATE_FLAG_QUESTIONS,
};
