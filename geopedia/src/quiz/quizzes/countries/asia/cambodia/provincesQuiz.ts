/**
 * Quiz configuration for Cambodia's first-level administrative divisions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CAMBODIA_PROVINCE_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${CAMBODIA_PROVINCE_QUESTIONS.length.toLocaleString()} first-level ` +
  `administrative divisions of Cambodia. Most are provinces, called ខេត្ត (Khaet), ` +
  `while Phnom Penh is the country's capital-level municipality.`;

export const cambodiaProvincesQuiz: FeatureQuiz = {
  id: "cambodia-provinces",
  name: "ខេត្ត - Khaet (Provinces)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "cambodia-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: CAMBODIA_PROVINCE_QUESTIONS,
};
