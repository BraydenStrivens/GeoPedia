/**
 * Quiz configuration for Brazil's municipalities.
 *
 * Questions can be grouped by state for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  BRAZIL_MUNICIPALITIES_BY_ID,
  BRAZIL_STATES_BY_ID,
} from "./data/admin";

const BRAZIL_MUNICIPALITY_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BRAZIL_MUNICIPALITIES_BY_ID).map(
    ([municipalityId, municipality]) => ({
      answer: municipalityId,
      display: municipality.name,
    }),
  );

const BRAZIL_STATE_NAME_VALUE_LABELS = Object.fromEntries(
  Object.entries(BRAZIL_STATES_BY_ID).map(([stateId, state]) => [
    stateId,
    state.name,
  ]),
);

/**
 * Description shown for Brazil's Municipalities quiz.
 */
const BRAZIL_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${BRAZIL_MUNICIPALITY_QUESTIONS.length} municipalities of ` +
  `Brazil, with state filtering to practice any desired subset.`;

/**
 * Quiz configuration for Brazil's municipalities.
 */
export const brazilMunicipalitiesQuiz: FeatureQuiz = {
  id: "brazil-municipalities",
  name: "Municipalities",
  description: BRAZIL_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "brazil-municipalities",

  answerProperty: "id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "state_id",
        label: "State",
        valueType: "string",
        valueLabels: BRAZIL_STATE_NAME_VALUE_LABELS,
      },
    ],
  },

  questions: BRAZIL_MUNICIPALITY_QUESTIONS,
};
