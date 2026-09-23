/**
 * Feature quiz for Kenya's 290 sub-counties.
 *
 * Questions use each sub-county's stable canonical ID as the answer.
 * Sub-counties can be grouped by their parent county.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { KENYA_SUB_COUNTIES_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  KENYA_SUB_COUNTIES_BY_ID,
).map(([subCountyId, subCounty]) => ({
  answer: subCountyId,
  display: subCounty.name,
}));

const COUNTY_VALUE_LABELS = Object.fromEntries(
  Object.values(KENYA_SUB_COUNTIES_BY_ID).map((subCounty) => [
    subCounty.countyId,
    subCounty.county,
  ]),
);

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} sub-counties of Kenya. ` +
  `Use county groups to study them in smaller regional sets.`;

export const kenyaSubCountiesQuiz: FeatureQuiz = {
  id: "kenya-sub-counties",
  name: "Sub-counties",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "kenya-sub-counties",

  answerProperty: "sub_county_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "county_id",
        label: "County",
        valueType: "string",
        valueLabels: COUNTY_VALUE_LABELS,
      },
    ],
  },

  questions: QUESTIONS,
};
