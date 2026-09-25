/**
 * Feature quiz configuration for South Africa's districts.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_DISTRICTS_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${SOUTH_AFRICA_DISTRICTS_QUIZ_QUESTIONS.length} districts ` +
  "of South Africa.";

export const southAfricaDistrictsQuiz: FeatureQuiz = {
  id: "south-africa-districts",
  name: "Districts",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-districts",

  answerProperty: "district_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
    ],
  },

  questions: SOUTH_AFRICA_DISTRICTS_QUIZ_QUESTIONS,
};
