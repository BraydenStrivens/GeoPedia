/**
 * Defines Chile's province quiz.
 *
 * Provinces can be grouped by their parent region for focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  CHILE_PROVINCES_BY_ID,
  CHILE_REGIONS_BY_ID,
} from "./data/admin";

const CHILE_PROVINCE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(CHILE_PROVINCES_BY_ID).map(
    ([provinceId, province]) => ({
      answer: provinceId,
      display: province.name,
    }),
  );

const CHILE_REGION_VALUE_LABELS: Record<string, string> =
  Object.fromEntries(
    Object.entries(CHILE_REGIONS_BY_ID).map(([regionId, region]) => [
      regionId,
      region,
    ]),
  );

const CHILE_PROVINCES_DESCRIPTION =
  `Learn all ${CHILE_PROVINCE_QUESTIONS.length} second-level administrative ` +
  `provinces of Chile. They can be grouped by region for more focused practice.`;

export const chileProvincesQuiz: FeatureQuiz = {
  id: "chile-provinces",
  name: "Provinces",
  description: CHILE_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "chile-provinces",

  answerProperty: "province_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: CHILE_REGION_VALUE_LABELS,
      },
    ],
  },

  questions: CHILE_PROVINCE_QUESTIONS,
};
