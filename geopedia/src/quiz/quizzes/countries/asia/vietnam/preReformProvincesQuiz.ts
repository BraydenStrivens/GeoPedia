/**
 * Quiz configuration for Vietnam's pre-reform first-level administrative
 * provinces and centrally governed municipalities.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { VIETNAM_PRE_REFORM_PROVINCE_QUESTIONS } from "./data/pre-reform-admin";

const DESCRIPTION =
  `Learn all ${VIETNAM_PRE_REFORM_PROVINCE_QUESTIONS.length.toLocaleString()} ` +
  `first-level provinces and municipalities of Vietnam before the 2025 reform. ` +
  `The reform reduced them from 63 to 34, but GeoGuessr coverage from before ` +
  `the reform still reflects the former boundaries.`;

export const vietnamPreReformProvincesQuiz: FeatureQuiz = {
  id: "vietnam-pre-reform-provinces",
  name: "Tỉnh & Thành phố (Provinces & Municipalities) — Pre-Reform",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "vietnam-pre-reform-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: VIETNAM_PRE_REFORM_PROVINCE_QUESTIONS,
};
