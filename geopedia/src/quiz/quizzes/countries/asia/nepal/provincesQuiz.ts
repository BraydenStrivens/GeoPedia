/**
 * Feature quiz for Nepal's 7 provinces (ADM1).
 *
 * Supports English and Nepali question labels and uses province
 * administrative codes as unique answers.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { nepalProvinceQuestions } from "./data/admin";

export const nepalProvincesQuiz: FeatureQuiz = {
  id: "nepal-provinces",
  name: "प्रदेश - Pradesh (Provinces)",
  description: "Learn the 7 provinces of Nepal.",

  quizTopic: "Administrative Regions",
  kind: "feature",

  mapId: "nepal-provinces",
  answerProperty: "admin_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: nepalProvinceQuestions,
};
