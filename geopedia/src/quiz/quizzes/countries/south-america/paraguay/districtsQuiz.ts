/**
 * Quiz configuration for Paraguay's second-level administrative districts.
 *
 * Questions can be grouped by department for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  PARAGUAY_DEPARTMENTS_BY_ID,
  PARAGUAY_DISTRICTS_BY_ID,
} from "./data/admin";

const PARAGUAY_DISTRICT_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(PARAGUAY_DISTRICTS_BY_ID).map(
    ([districtId, district]) => ({
      answer: districtId,
      display: district.name,
    }),
  );

const PARAGUAY_DEPARTMENT_VALUE_LABELS: Record<string, string> = {
  ...PARAGUAY_DEPARTMENTS_BY_ID,
};

const PARAGUAY_DISTRICTS_DESCRIPTION =
  `Learn all ${PARAGUAY_DISTRICT_QUESTIONS.length} districts in the ` +
  `Paraguay administrative boundary dataset. Districts can be grouped by ` +
  `department to practice smaller sections of the country.`;

export const paraguayDistrictsQuiz: FeatureQuiz = {
  id: "paraguay-districts",
  name: "Districts",
  description: PARAGUAY_DISTRICTS_DESCRIPTION,

  kind: "feature",
  mapId: "paraguay-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "department_id",
        label: "Department",
        valueType: "string",
        valueLabels: PARAGUAY_DEPARTMENT_VALUE_LABELS,
      },
    ],
  },

  questions: PARAGUAY_DISTRICT_QUESTIONS,
};
