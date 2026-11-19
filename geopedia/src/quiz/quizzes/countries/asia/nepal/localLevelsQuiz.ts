/**
 * Feature quiz for Nepal's 753 local levels (ADM3).
 *
 * Includes rural municipalities, municipalities, sub-metropolitan
 * cities, and metropolitan cities.
 *
 * Supports English and Nepali question labels and uses municipality
 * administrative codes as unique answers.
 *
 * Supports grouping by province, district, and local level type.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { nepalLocalLevelQuestions } from "./data/admin";

const description =
  `Learn the 753 local levels of Nepal, including rural municipalities, ` +
  `municipalities, sub-metropolitan cities, and metropolitan cities.`;

export const nepalLocalLevelsQuiz: FeatureQuiz = {
  id: "nepal-local-levels",
  name: "स्थानीय तह - Sthaniya Taha (Local Levels)",
  description: description,

  quizTopic: "Administrative Regions",
  kind: "feature",

  mapId: "nepal-local-levels",
  answerProperty: "admin_id",
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
        property: "type",
        label: "Type",
        valueType: "string",
      },
    ],
  },

  questions: nepalLocalLevelQuestions,
};
