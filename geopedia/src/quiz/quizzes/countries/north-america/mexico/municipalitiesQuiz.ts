/**
 * Quiz configuration for Mexico's municipalities.
 *
 * INEGI municipality IDs are used as answer values so municipalities remain
 * uniquely identifiable. Questions can be grouped by state for more focused
 * practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  MEXICO_MUNICIPALITIES_BY_ID,
  MEXICO_STATES_BY_ID,
} from "./data/admin";

const MEXICO_MUNICIPALITY_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(MEXICO_MUNICIPALITIES_BY_ID).map(
    ([municipalityId, municipality]) => ({
      answer: municipalityId,
      display: municipality.name,
    }),
  );

const MEXICO_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${MEXICO_MUNICIPALITY_QUESTIONS.length} municipalities of Mexico, ` +
  `with filters that let you practice municipalities from any desired state or ` +
  `combination of states.`;

export const mexicoMunicipalitiesQuiz: FeatureQuiz = {
  id: "mexico-municipalities",
  name: "Municipalities",
  description: MEXICO_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "mexico-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "state_id",
        label: "State",
        valueType: "string",
        valueLabels: MEXICO_STATES_BY_ID,
      },
    ],
  },

  questions: MEXICO_MUNICIPALITY_QUESTIONS,
};
