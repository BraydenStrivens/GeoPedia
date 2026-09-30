/**
 * Quiz configuration for Malaysia's third-level administrative sub-districts.
 *
 * Sub-districts can be grouped by their parent state or federal territory and
 * district for progressively more focused practice.
 */

import { FeatureQuiz } from "@/types/quiz";

import { MALAYSIA_SUB_DISTRICT_QUESTIONS } from "./data/admin";

const MALAYSIA_SUB_DISTRICTS_DESCRIPTION =
  `Learn all ${MALAYSIA_SUB_DISTRICT_QUESTIONS.length.toLocaleString()} third-level administrative ` +
  `divisions of Malaysia. Common Malay terms include mukim (sub-district), pekan (town), ` +
  `and bandar (town/city); group them by state or district for more focused practice.`;

export const malaysiaSubDistrictsQuiz: FeatureQuiz = {
  id: "malaysia-sub-districts",
  name: "Mukim (Sub-Districts)",
  description: MALAYSIA_SUB_DISTRICTS_DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "malaysia-sub-districts",

  answerProperty: "sub_district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "state",
        label: "State / Federal Territory",
        valueType: "string",
      },
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
    ],
  },

  questions: MALAYSIA_SUB_DISTRICT_QUESTIONS,
};
