/**
 * Quiz configuration for Colombia's first-level administrative departments.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COLOMBIA_DEPARTMENTS_BY_ID } from "./data/admin";

const COLOMBIA_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(COLOMBIA_DEPARTMENTS_BY_ID).map(
    ([departmentId, department]) => ({
      answer: departmentId,
      display: department,
    }),
  );

const COLOMBIA_DEPARTMENTS_DESCRIPTION =
  `Learn all ${COLOMBIA_DEPARTMENT_QUESTIONS.length} department-level ` +
  `divisions of Colombia, including Bogotá D.C.`;

export const colombiaDepartmentsQuiz: FeatureQuiz = {
  id: "colombia-departments",
  name: "Departments",
  description: COLOMBIA_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "colombia-departments",

  answerProperty: "id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: COLOMBIA_DEPARTMENT_QUESTIONS,
};
