/**
 * Quiz configuration for Peru's second-level administrative provinces.
 *
 * Questions can be grouped by region for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  PERU_PROVINCES_BY_ID,
  PERU_REGIONS_BY_ID,
} from "./data/admin";

const PERU_PROVINCE_QUESTIONS = Object.entries(
  PERU_PROVINCES_BY_ID,
).map(([provinceId, province]) => ({
  answer: provinceId,
  display: province.name,
}));

const PERU_PROVINCES_DESCRIPTION =
  `Learn all ${PERU_PROVINCE_QUESTIONS.length} provinces of Peru. ` +
  `Use region groups to study the provinces in smaller geographic sets.`;

export const peruProvincesQuiz: FeatureQuiz = {
  id: "peru-provinces",
  name: "Provinces",
  description: PERU_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "peru-provinces",

  answerProperty: "province_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: PERU_REGIONS_BY_ID,
      },
    ],
  },

  questions: PERU_PROVINCE_QUESTIONS,
};
