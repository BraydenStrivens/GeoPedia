/**
 * Feature quiz configuration for South Africa's provinces.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { SOUTH_AFRICA_PROVINCES_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${SOUTH_AFRICA_PROVINCES_QUIZ_QUESTIONS.length} provinces ` +
  "of South Africa.";

export const southAfricaProvincesQuiz: FeatureQuiz = {
  id: "south-africa-provinces",
  name: "Provinces",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-africa-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
    subdivisionLabels: false,
  },

  questions: SOUTH_AFRICA_PROVINCES_QUIZ_QUESTIONS,
};
