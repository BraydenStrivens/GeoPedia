/**
 * Feature quiz for Nigeria's 774 Local Government Areas.
 *
 * LGAs can be practiced by state, and duplicated LGA names are disambiguated
 * in question text using their parent state.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  NIGERIA_LGAS_BY_ID,
  NIGERIA_STATES_BY_ID,
} from "./data/admin";

const QUESTIONS: FeatureQuiz["questions"] = Object.entries(
  NIGERIA_LGAS_BY_ID,
).map(([lgaId, lga]) => ({
  answer: lgaId,
  display: lga.display,
}));

const STATE_VALUE_LABELS = Object.fromEntries(
  Object.entries(NIGERIA_STATES_BY_ID).map(([stateId, state]) => [
    stateId,
    state.name,
  ]),
);

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} Local Government Areas (LGAs) of Nigeria, grouped ` +
  `by state and the Federal Capital Territory.`;

export const nigeriaLocalGovernmentAreasQuiz: FeatureQuiz = {
  id: "nigeria-local-government-areas",
  name: "Local Government Areas",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "nigeria-local-government-areas",

  answerProperty: "lga_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
  },

  grouping: {
    properties: [
      {
        property: "state_id",
        label: "State",
        valueType: "string",
        valueLabels: STATE_VALUE_LABELS,
      },
    ],
  },

  questions: QUESTIONS,
};
