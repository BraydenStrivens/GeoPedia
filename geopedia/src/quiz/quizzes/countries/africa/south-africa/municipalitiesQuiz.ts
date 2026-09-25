/**
 * Feature quiz configuration for South Africa's municipalities.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_MUNICIPALITIES_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${SOUTH_AFRICA_MUNICIPALITIES_QUIZ_QUESTIONS.length} ` +
  "municipalities of South Africa.";

export const southAfricaMunicipalitiesQuiz: FeatureQuiz = {
  id: "south-africa-municipalities",
  name: "Municipalities",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
    ],
  },

  questions: SOUTH_AFRICA_MUNICIPALITIES_QUIZ_QUESTIONS,
};
