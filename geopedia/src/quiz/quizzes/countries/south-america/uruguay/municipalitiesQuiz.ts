/**
 * Quiz configuration for Uruguay's municipalities.
 *
 * Municipality boundaries do not cover the entire country because some areas
 * of Uruguay are not incorporated into a municipality. Questions can be
 * grouped by department for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  URUGUAY_DEPARTMENTS_BY_ID,
  URUGUAY_MUNICIPALITIES_BY_ID,
} from "./data/admin";

const URUGUAY_MUNICIPALITY_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(URUGUAY_MUNICIPALITIES_BY_ID).map(
    ([municipalityId, municipality]) => ({
      answer: municipalityId,
      display: municipality.name,
    }),
  );

const URUGUAY_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${URUGUAY_MUNICIPALITY_QUESTIONS.length} municipalities of ` +
  `Uruguay by identifying each municipality on the map. Some areas of ` +
  `Uruguay are not part of a municipality, so the municipality boundaries ` +
  `do not cover the entire country.`;

export const uruguayMunicipalitiesQuiz: FeatureQuiz = {
  id: "uruguay-municipalities",
  name: "Municipalities",
  description: URUGUAY_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "uruguay-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: URUGUAY_DEPARTMENTS_BY_ID,
      },
    ],
  },

  questions: URUGUAY_MUNICIPALITY_QUESTIONS,
};
