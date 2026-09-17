/**
 * Quiz for identifying Guatemala's departments.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { GUATEMALA_DEPARTMENTS_BY_ID } from "./data/admin";

const GUATEMALA_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(GUATEMALA_DEPARTMENTS_BY_ID).map(
    ([answer, display]) => ({
      answer,
      display,
    }),
  );

const GUATEMALA_DEPARTMENTS_DESCRIPTION = `Learn all ${GUATEMALA_DEPARTMENT_QUESTIONS.length} departments of Guatemala.`;

export const guatemalaDepartmentsQuiz: FeatureQuiz = {
  id: "guatemala-departments",
  name: "Departments",
  description: GUATEMALA_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "guatemala-departments",

  answerProperty: "department_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: GUATEMALA_DEPARTMENT_QUESTIONS,
};
