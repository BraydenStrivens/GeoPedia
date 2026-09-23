/**
 * Feature quiz for Uganda's sub-counties.
 *
 * Sub-counties can be grouped by region, district, or county. Stable
 * sub-county IDs are used as answers because many names occur more than once.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { UGANDA_SUB_COUNTIES_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn all ${UGANDA_SUB_COUNTIES_QUIZ_QUESTIONS.length} sub-counties of Uganda.`;

export const ugandaSubCountiesQuiz: FeatureQuiz = {
  id: "uganda-sub-counties",
  name: "Sub-counties",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "uganda-sub-counties",

  answerProperty: "sub_county_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
      {
        property: "county",
        label: "County",
        valueType: "string",
      },
    ],
  },

  questions: UGANDA_SUB_COUNTIES_QUIZ_QUESTIONS,
};
