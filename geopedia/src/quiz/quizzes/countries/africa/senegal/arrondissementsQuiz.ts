/**
 * Defines Senegal's arrondissement quiz.
 *
 * Arrondissements can be grouped by their parent department or region for
 * focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  SENEGAL_ARRONDISSEMENTS_BY_ID,
  SENEGAL_DEPARTMENTS_BY_ID,
  SENEGAL_REGIONS_BY_ID,
} from "./data/admin";

const SENEGAL_ARRONDISSEMENT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(SENEGAL_ARRONDISSEMENTS_BY_ID).map(
    ([arrondissementId, arrondissement]) => ({
      answer: arrondissementId,
      display: arrondissement.name,
    }),
  );

const SENEGAL_DEPARTMENT_VALUE_LABELS: Record<string, string> =
  Object.fromEntries(
    Object.entries(SENEGAL_DEPARTMENTS_BY_ID).map(
      ([departmentId, department]) => [departmentId, department.name],
    ),
  );

const SENEGAL_REGION_VALUE_LABELS: Record<string, string> =
  Object.fromEntries(
    Object.entries(SENEGAL_REGIONS_BY_ID).map(
      ([regionId, region]) => [regionId, region],
    ),
  );

const SENEGAL_ARRONDISSEMENTS_DESCRIPTION =
  `Learn all ${SENEGAL_ARRONDISSEMENT_QUESTIONS.length} third-level administrative ` +
  `arrondissements of Senegal. They can be grouped by department or region for ` +
  `more focused practice.`;

export const senegalArrondissementsQuiz: FeatureQuiz = {
  id: "senegal-arrondissements",
  name: "Arrondissements",
  description: SENEGAL_ARRONDISSEMENTS_DESCRIPTION,

  kind: "feature",
  mapId: "senegal-arrondissements",

  answerProperty: "arrondissement_id",
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
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: SENEGAL_DEPARTMENT_VALUE_LABELS,
      },
    ],
  },

  questions: SENEGAL_ARRONDISSEMENT_QUESTIONS,
};
