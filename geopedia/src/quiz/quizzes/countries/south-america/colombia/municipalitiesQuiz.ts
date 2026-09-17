/**
 * Quiz configuration for Colombia's second-level administrative municipalities.
 *
 * Questions can be grouped by department for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  COLOMBIA_DEPARTMENTS_BY_ID,
  COLOMBIA_MUNICIPALITIES_BY_ID,
} from "./data/admin";

const COLOMBIA_MUNICIPALITY_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(COLOMBIA_MUNICIPALITIES_BY_ID).map(
    ([municipalityId, municipality]) => ({
      answer: municipalityId,
      display: municipality.name,
    }),
  );

const COLOMBIA_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${COLOMBIA_MUNICIPALITY_QUESTIONS.length} municipalities of ` +
  `Colombia, with department filtering to practice any desired subset.`;

export const colombiaMunicipalitiesQuiz: FeatureQuiz = {
  id: "colombia-municipalities",
  name: "Municipalities",
  description: COLOMBIA_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-municipalities",

  answerProperty: "id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: COLOMBIA_DEPARTMENTS_BY_ID,
      },
    ],
  },

  questions: COLOMBIA_MUNICIPALITY_QUESTIONS,
};
