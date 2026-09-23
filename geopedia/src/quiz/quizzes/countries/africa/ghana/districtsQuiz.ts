/**
 * Feature quiz for Ghana's second-level administrative districts.
 *
 * District questions can be grouped by their parent administrative region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  GHANA_DISTRICTS_BY_ID,
  GHANA_REGIONS_BY_ID,
} from "./data/admin";

const QUESTIONS: FeatureQuiz["questions"] = Object.entries(
  GHANA_DISTRICTS_BY_ID,
).map(([districtId, district]) => ({
  answer: districtId,
  display: district.name,
}));

const REGION_VALUE_LABELS = Object.fromEntries(
  Object.entries(GHANA_REGIONS_BY_ID).map(([regionId, region]) => [
    regionId,
    region.name,
  ]),
);

const DESCRIPTION = `Learn all ${QUESTIONS.length} second-level administrative districts of Ghana.`;

export const ghanaDistrictsQuiz: FeatureQuiz = {
  id: "ghana-districts",
  name: "Districts",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "ghana-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: REGION_VALUE_LABELS,
      },
    ],
  },

  questions: QUESTIONS,
};
