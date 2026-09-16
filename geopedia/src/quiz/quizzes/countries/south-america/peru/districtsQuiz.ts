/**
 * Quiz configuration for Peru's third-level administrative districts.
 *
 * Questions can be grouped by region or province for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  PERU_DISTRICTS_BY_ID,
  PERU_PROVINCES_BY_ID,
  PERU_REGIONS_BY_ID,
} from "./data/admin";

const PERU_DISTRICT_QUESTIONS = Object.entries(
  PERU_DISTRICTS_BY_ID,
).map(([districtId, district]) => ({
  answer: districtId,
  display: district.name,
}));

const PERU_DISTRICTS_DESCRIPTION =
  `Learn all ${PERU_DISTRICT_QUESTIONS.length} districts of Peru. ` +
  `Use region and province groups to break the country into smaller study sets.`;

export const PERU_PROVINCE_VALUE_LABELS = Object.fromEntries(
  Object.entries(PERU_PROVINCES_BY_ID).map(
    ([provinceId, province]) => [provinceId, province.name],
  ),
);

export const peruDistrictsQuiz: FeatureQuiz = {
  id: "peru-districts",
  name: "Districts",
  description: PERU_DISTRICTS_DESCRIPTION,

  kind: "feature",
  mapId: "peru-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: PERU_REGIONS_BY_ID,
      },
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: PERU_PROVINCE_VALUE_LABELS,
      },
    ],
  },

  questions: PERU_DISTRICT_QUESTIONS,
};
