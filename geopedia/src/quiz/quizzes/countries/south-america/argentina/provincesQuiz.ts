import type { FeatureQuiz } from "@/types/quiz";

import { ARGENTINA_PROVINCES_BY_ID } from "./data/admin";

const ARGENTINA_PROVINCE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(ARGENTINA_PROVINCES_BY_ID).map(
    ([provinceId, province]) => ({
      answer: provinceId,
      display: province.display,
    }),
  );

const ARGENTINA_PROVINCES_DESCRIPTION =
  `Learn all ${ARGENTINA_PROVINCE_QUESTIONS.length} first-level administrative ` +
  `divisions of Argentina, including its 23 provinces and the Autonomous City ` +
  `of Buenos Aires.`;

export const argentinaProvincesQuiz: FeatureQuiz = {
  id: "argentina-provinces",
  name: "Provinces",
  description: ARGENTINA_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "argentina-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: ARGENTINA_PROVINCE_QUESTIONS,
};
