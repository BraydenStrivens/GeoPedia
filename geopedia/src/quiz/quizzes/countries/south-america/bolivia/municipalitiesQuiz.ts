/**
 * Quiz configuration for Bolivia's third-level administrative municipalities.
 *
 * Questions can be grouped by department or province for more focused
 * practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  BOLIVIA_DEPARTMENTS_BY_ID,
  BOLIVIA_MUNICIPALITIES_BY_ID,
  BOLIVIA_PROVINCES_BY_ID,
} from "./data/admin";

const BOLIVIA_MUNICIPALITY_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BOLIVIA_MUNICIPALITIES_BY_ID).map(
    ([municipalityId, municipality]) => ({
      answer: municipalityId,
      display: municipality.name,
    }),
  );

const BOLIVIA_DEPARTMENT_VALUE_LABELS: Record<string, string> = {
  ...BOLIVIA_DEPARTMENTS_BY_ID,
};

const BOLIVIA_PROVINCE_VALUE_LABELS: Record<string, string> =
  Object.fromEntries(
    Object.entries(BOLIVIA_PROVINCES_BY_ID).map(
      ([provinceId, province]) => [provinceId, province.name],
    ),
  );

const BOLIVIA_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${BOLIVIA_MUNICIPALITY_QUESTIONS.length} municipalities of ` +
  `Bolivia. Municipalities are Bolivia's third-level administrative ` +
  `divisions and can be grouped by department or province for more focused ` +
  `practice.`;

export const boliviaMunicipalitiesQuiz: FeatureQuiz = {
  id: "bolivia-municipalities",
  name: "Municipalities",
  description: BOLIVIA_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "bolivia-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: BOLIVIA_DEPARTMENT_VALUE_LABELS,
      },
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: BOLIVIA_PROVINCE_VALUE_LABELS,
      },
    ],
  },

  questions: BOLIVIA_MUNICIPALITY_QUESTIONS,
};
