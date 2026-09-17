/**
 * Quiz for identifying Guatemala's municipalities.
 *
 * Municipalities can be grouped by their parent department. Duplicate
 * municipality names are disambiguated by their department.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  GUATEMALA_DEPARTMENTS_BY_ID,
  GUATEMALA_MUNICIPALITIES_BY_ID,
} from "./data/admin";

const GUATEMALA_MUNICIPALITY_QUESTIONS = Object.entries(
  GUATEMALA_MUNICIPALITIES_BY_ID,
).map(([municipalityId, municipality]) => ({
  answer: municipalityId,
  display: municipality.name,
}));

const GUATEMALA_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${GUATEMALA_MUNICIPALITY_QUESTIONS.length} municipalities of ` +
  `Guatemala, with filters that let you practice municipalities from any ` +
  `desired department or combination of departments.`;

export const guatemalaMunicipalitiesQuiz: FeatureQuiz = {
  id: "guatemala-municipalities",
  name: "Municipalities",
  description: GUATEMALA_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "guatemala-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: GUATEMALA_DEPARTMENTS_BY_ID,
      },
    ],
  },

  questions: GUATEMALA_MUNICIPALITY_QUESTIONS,
};
