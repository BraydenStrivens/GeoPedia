/**
 * Quiz configuration for Indonesia's third-level kecamatan.
 *
 * Sub-districts can be grouped by region, province, or regency/city.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_SUB_DISTRICT_QUESTIONS } from "./data/sub-districts";

const INDONESIA_SUB_DISTRICTS_DESCRIPTION =
  `Learn all ${INDONESIA_SUB_DISTRICT_QUESTIONS.length.toLocaleString()} ` +
  `sub-districts of Indonesia. They can be grouped ` +
  `by region, province, or regency/city for more focused practice.`;

export const indonesiaSubDistrictsQuiz: FeatureQuiz = {
  id: "indonesia-sub-districts",
  name: "Kecamatan (Sub-Districts)",
  description: INDONESIA_SUB_DISTRICTS_DESCRIPTION,

  kind: "feature",
  mapId: "indonesia-sub-districts",

  answerProperty: "sub_district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "regency",
        label: "Regency / City",
        valueType: "string",
      },
    ],
  },

  questions: INDONESIA_SUB_DISTRICT_QUESTIONS,
};
