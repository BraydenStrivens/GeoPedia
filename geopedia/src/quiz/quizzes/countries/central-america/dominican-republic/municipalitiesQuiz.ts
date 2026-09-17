/**
 * Quiz for identifying the Dominican Republic's municipalities.
 *
 * Municipalities can be grouped by their parent province or region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  DOMINICAN_REPUBLIC_MUNICIPALITIES_BY_ID,
  DOMINICAN_REPUBLIC_PROVINCES_BY_ID,
  DOMINICAN_REPUBLIC_REGIONS_BY_ID,
} from "./data/admin";

const DOMINICAN_REPUBLIC_MUNICIPALITY_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(DOMINICAN_REPUBLIC_MUNICIPALITIES_BY_ID).map(
    ([answer, municipality]) => ({
      answer,
      display: municipality.name,
    }),
  );

const DOMINICAN_REPUBLIC_PROVINCE_NAME_VALUE_LABELS =
  Object.fromEntries(
    Object.entries(DOMINICAN_REPUBLIC_PROVINCES_BY_ID).map(
      ([provinceId, province]) => [provinceId, province.name],
    ),
  );

const DOMINICAN_REPUBLIC_MUNICIPALITIES_DESCRIPTION =
  `Learn all ${DOMINICAN_REPUBLIC_MUNICIPALITY_QUESTIONS.length} municipalities ` +
  `of the Dominican Republic, with filters that let you practice municipalities ` +
  `by province or region.`;

export const dominicanRepublicMunicipalitiesQuiz: FeatureQuiz = {
  id: "dominican-republic-municipalities",
  name: "Dominican Republic Municipalities",
  description: DOMINICAN_REPUBLIC_MUNICIPALITIES_DESCRIPTION,

  kind: "feature",
  mapId: "dominican-republic-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "province_id",
        label: "Province",
        valueType: "string",
        valueLabels: DOMINICAN_REPUBLIC_PROVINCE_NAME_VALUE_LABELS,
      },
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: DOMINICAN_REPUBLIC_REGIONS_BY_ID,
      },
    ],
  },

  questions: DOMINICAN_REPUBLIC_MUNICIPALITY_QUESTIONS,
};
