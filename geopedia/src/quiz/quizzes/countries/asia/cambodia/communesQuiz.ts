/**
 * Quiz configuration for Cambodia's third-level administrative divisions.
 *
 * Communes can be grouped by their parent province or district for
 * focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CAMBODIA_COMMUNE_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${CAMBODIA_COMMUNE_QUESTIONS.length.toLocaleString()} third-level ` +
  `administrative divisions of Cambodia. These primarily include ឃុំ (Khum) communes ` +
  `and សង្កាត់ (Sangkat) urban communes, and can be grouped by province or district.`;

export const cambodiaCommunesQuiz: FeatureQuiz = {
  id: "cambodia-communes",
  name: "ឃុំ · សង្កាត់ - Khum · Sangkat (Communes)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "cambodia-communes",

  answerProperty: "commune_id",
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

  questions: CAMBODIA_COMMUNE_QUESTIONS,
};
