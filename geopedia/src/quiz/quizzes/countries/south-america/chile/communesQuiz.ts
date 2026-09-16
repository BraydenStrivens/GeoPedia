/**
 * Defines Chile's commune quiz.
 *
 * Communes can be grouped by their parent province or region for focused
 * practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  CHILE_COMMUNES_BY_ID,
  CHILE_PROVINCES_BY_ID,
  CHILE_REGIONS_BY_ID,
} from "./data/admin";

const CHILE_COMMUNE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(CHILE_COMMUNES_BY_ID).map(
    ([communeId, commune]) => ({
      answer: communeId,
      display: commune.name,
    }),
  );

const CHILE_PROVINCE_VALUE_LABELS: Record<string, string> =
  Object.fromEntries(
    Object.entries(CHILE_PROVINCES_BY_ID).map(
      ([provinceId, province]) => [provinceId, province.name],
    ),
  );

const CHILE_REGION_VALUE_LABELS: Record<string, string> =
  Object.fromEntries(
    Object.entries(CHILE_REGIONS_BY_ID).map(([regionId, region]) => [
      regionId,
      region,
    ]),
  );

const CHILE_COMMUNES_DESCRIPTION =
  `Learn all ${CHILE_COMMUNE_QUESTIONS.length} third-level administrative ` +
  `communes of Chile. They can be grouped by province or region for more ` +
  `focused practice.`;

export const chileCommunesQuiz: FeatureQuiz = {
  id: "chile-communes",
  name: "Communes",
  description: CHILE_COMMUNES_DESCRIPTION,

  kind: "feature",
  mapId: "chile-communes",

  answerProperty: "commune_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: CHILE_PROVINCE_VALUE_LABELS,
      },
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: CHILE_REGION_VALUE_LABELS,
      },
    ],
  },

  questions: CHILE_COMMUNE_QUESTIONS,
};
