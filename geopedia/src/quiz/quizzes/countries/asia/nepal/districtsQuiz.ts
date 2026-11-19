/**
 * Feature quiz for Nepal's 77 districts (ADM2).
 *
 * Supports English and Nepali question labels and uses district
 * administrative codes as unique answers.
 *
 * Supports administrative grouping by province.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { nepalDistrictQuestions } from "./data/admin";

export const nepalDistrictsQuiz: FeatureQuiz = {
  id: "nepal-districts",
  name: "जिल्ला - Jilla (Districts)",
  description: "Learn the 77 districts of Nepal.",

  quizTopic: "Administrative Regions",
  kind: "feature",

  mapId: "nepal-districts",
  answerProperty: "admin_id",
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

  questions: nepalDistrictQuestions,
};
