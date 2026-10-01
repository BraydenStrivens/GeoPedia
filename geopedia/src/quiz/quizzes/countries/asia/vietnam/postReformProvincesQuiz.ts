/**
 * Quiz configuration for Vietnam's post-reform first-level administrative
 * provinces and centrally governed cities.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_POST_REFORM_PROVINCE_QUESTIONS } from "./data/post-reform-admin";

const DESCRIPTION =
  `Learn all ${VIETNAM_POST_REFORM_PROVINCE_QUESTIONS.length.toLocaleString()} ` +
  `first-level provinces and cities of Vietnam after the 2025 reform, which ` +
  `reduced the number of first-level units from 63 to 34. These boundaries ` +
  `apply to coverage captured after the reform.`;

export const vietnamPostReformProvincesQuiz: FeatureQuiz = {
  id: "vietnam-post-reform-provinces",
  name: "Tỉnh & Thành phố (Provinces & Cities) — Post-Reform",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "vietnam-post-reform-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: VIETNAM_POST_REFORM_PROVINCE_QUESTIONS,
};
