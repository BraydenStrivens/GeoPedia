/**
 * Quiz configuration for Bolivia's second-level administrative provinces.
 *
 * Questions can be grouped by department for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  BOLIVIA_DEPARTMENTS_BY_ID,
  BOLIVIA_PROVINCES_BY_ID,
} from "./data/admin";

const BOLIVIA_PROVINCE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(BOLIVIA_PROVINCES_BY_ID).map(
    ([provinceId, province]) => ({
      answer: provinceId,
      display: province.name,
    }),
  );

const BOLIVIA_DEPARTMENT_VALUE_LABELS: Record<string, string> =
  BOLIVIA_DEPARTMENTS_BY_ID;

const BOLIVIA_PROVINCES_DESCRIPTION =
  `Learn all ${BOLIVIA_PROVINCE_QUESTIONS.length} provinces of Bolivia. ` +
  `Provinces are Bolivia's second-level administrative divisions and can be ` +
  `grouped by department to practice the country in smaller sections.`;

export const boliviaProvincesQuiz: FeatureQuiz = {
  id: "bolivia-provinces",
  name: "Provinces",
  description: BOLIVIA_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "bolivia-provinces",

  answerProperty: "province_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: BOLIVIA_DEPARTMENT_VALUE_LABELS,
      },
    ],
  },

  questions: BOLIVIA_PROVINCE_QUESTIONS,
};
