/**
 * Feature quiz for Kenya's 1,452 wards.
 *
 * Questions use each ward's stable canonical ID as the answer. Duplicate ward
 * names use the generated hierarchy-aware display where the source data allows
 * them to be distinguished. Wards can be grouped by county or sub-county.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { KENYA_WARDS_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  KENYA_WARDS_BY_ID,
).map(([wardId, ward]) => ({
  answer: wardId,
  display: ward.display,
}));

const COUNTY_VALUE_LABELS = Object.fromEntries(
  Object.values(KENYA_WARDS_BY_ID).map((ward) => [
    ward.countyId,
    ward.county,
  ]),
);

const SUB_COUNTY_VALUE_LABELS = Object.fromEntries(
  Object.values(KENYA_WARDS_BY_ID).map((ward) => [
    ward.subCountyId,
    ward.subCounty,
  ]),
);

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} wards of Kenya. ` +
  `Use county and sub-county groups to study them in smaller regional sets.`;

export const kenyaWardsQuiz: FeatureQuiz = {
  id: "kenya-wards",
  name: "Wards",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "kenya-wards",

  answerProperty: "ward_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "county_id",
        label: "County",
        valueType: "string",
        valueLabels: COUNTY_VALUE_LABELS,
      },
      {
        property: "sub_county_id",
        label: "Sub-county",
        valueType: "string",
        valueLabels: SUB_COUNTY_VALUE_LABELS,
      },
    ],
  },

  questions: QUESTIONS,
};
