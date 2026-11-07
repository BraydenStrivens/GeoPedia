/**
 * Feature quiz for Thailand's 928 district-level divisions.
 *
 * Includes amphoe throughout the provinces and khet in Bangkok.
 * Questions can be grouped by their parent province-level division.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { THAILAND_DISTRICT_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${THAILAND_DISTRICT_QUESTIONS.length.toLocaleString()} district-level divisions of Thailand. ` +
  `Most are amphoe (districts), while Bangkok uses khet. Group them by province to study smaller sets.`;

export const thailandDistrictsQuiz: FeatureQuiz = {
  id: "thailand-districts",
  name: "อำเภอ - Amphoe (Districts)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "thailand-districts",

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

  questions: THAILAND_DISTRICT_QUESTIONS,
};
