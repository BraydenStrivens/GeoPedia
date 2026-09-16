/**
 * Quiz configuration for Argentina's second-level administrative divisions.
 *
 * Includes departments, Buenos Aires Province's partidos, and the communes
 * of the Autonomous City of Buenos Aires. Questions can be grouped by
 * first-level administrative division.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  ARGENTINA_DEPARTMENTS_BY_ID,
  ARGENTINA_PROVINCES_BY_ID,
} from "./data/admin";

const ARGENTINA_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(ARGENTINA_DEPARTMENTS_BY_ID).map(
    ([departmentId, department]) => ({
      answer: departmentId,
      display: department.name,
    }),
  );

const ARGENTINA_PROVINCE_VALUE_LABELS: Record<string, string> =
  Object.fromEntries(Object.entries(ARGENTINA_PROVINCES_BY_ID));

const ARGENTINA_DEPARTMENTS_DESCRIPTION =
  `Learn all ${ARGENTINA_DEPARTMENT_QUESTIONS.length} second-level ` +
  `administrative divisions of Argentina. This includes departments, Buenos ` +
  `Aires Province's partidos, and the communes of the Autonomous City of ` +
  `Buenos Aires. They can be grouped by province for more focused practice.`;

export const argentinaDepartmentsQuiz: FeatureQuiz = {
  id: "argentina-departments",
  name: "Departments",
  description: ARGENTINA_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "argentina-departments",

  answerProperty: "department_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: ARGENTINA_PROVINCE_VALUE_LABELS,
      },
    ],
  },

  questions: ARGENTINA_DEPARTMENT_QUESTIONS,
};
