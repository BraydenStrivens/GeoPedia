/**
 * Defines Senegal's department quiz.
 *
 * Departments can be grouped by their parent region for focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  SENEGAL_DEPARTMENTS_BY_ID,
  SENEGAL_REGIONS_BY_ID,
} from "./data/admin";

const SENEGAL_DEPARTMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(SENEGAL_DEPARTMENTS_BY_ID).map(
    ([departmentId, department]) => ({
      answer: departmentId,
      display: department.name,
    }),
  );

const SENEGAL_REGION_VALUE_LABELS: Record<string, string> =
  Object.fromEntries(
    Object.entries(SENEGAL_REGIONS_BY_ID).map(
      ([regionId, region]) => [regionId, region],
    ),
  );

const SENEGAL_DEPARTMENTS_DESCRIPTION =
  `Learn all ${SENEGAL_DEPARTMENT_QUESTIONS.length} second-level administrative ` +
  `departments of Senegal. They can be grouped by region for more focused practice.`;

export const senegalDepartmentsQuiz: FeatureQuiz = {
  id: "senegal-departments",
  name: "Departments",
  description: SENEGAL_DEPARTMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "senegal-departments",

  answerProperty: "department_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
    subdivisionBorders: false,
  },

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: SENEGAL_REGION_VALUE_LABELS,
      },
    ],
  },

  questions: SENEGAL_DEPARTMENT_QUESTIONS,
};
