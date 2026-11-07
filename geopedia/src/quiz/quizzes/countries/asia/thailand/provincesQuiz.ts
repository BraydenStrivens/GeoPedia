/**
 * Feature quiz for Thailand's 76 provinces and Bangkok.
 *
 * Questions use stable administrative IDs and provide English and
 * Thai names for all 77 province-level divisions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { THAILAND_PROVINCE_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${THAILAND_PROVINCE_QUESTIONS.length.toLocaleString()} province-level divisions of Thailand. ` +
  `Thailand has 76 changwat (provinces) and Bangkok, a special administrative area.`;

export const thailandProvincesQuiz: FeatureQuiz = {
  id: "thailand-provinces",
  name: "จังหวัด - Changwat (Provinces)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "thailand-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: THAILAND_PROVINCE_QUESTIONS,
};
