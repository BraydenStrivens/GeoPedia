/**
 * Feature quiz configuration for South Africa's wards.
 *
 * Wards can be grouped by province, district, or municipality so the large
 * national question set can be studied in smaller administrative groups.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_WARDS_QUIZ_QUESTIONS } from "./data/wards";

const DESCRIPTION =
  `Learn all ${SOUTH_AFRICA_WARDS_QUIZ_QUESTIONS.length} wards ` +
  "of South Africa.";

export const southAfricaWardsQuiz: FeatureQuiz = {
  id: "south-africa-wards",
  name: "Wards",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-wards",

  answerProperty: "ward_id",
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
      {
        property: "municipality",
        label: "Municipality",
        valueType: "string",
      },
    ],
  },

  questions: SOUTH_AFRICA_WARDS_QUIZ_QUESTIONS,
};
