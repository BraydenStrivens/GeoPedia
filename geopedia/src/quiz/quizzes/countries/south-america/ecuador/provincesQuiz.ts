/**
 * Quiz configuration for Ecuador's first-level administrative provinces.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ECUADOR_PROVINCES_BY_ID } from "./data/admin";

const ECUADOR_PROVINCE_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(ECUADOR_PROVINCES_BY_ID).map(
    ([provinceId, province]) => ({
      answer: provinceId,
      display: province,
    }),
  );

const ECUADOR_PROVINCES_DESCRIPTION =
  `Learn all ${ECUADOR_PROVINCE_QUESTIONS.length} provinces of Ecuador and ` +
  `where they are located across the country.`;

export const ecuadorProvincesQuiz: FeatureQuiz = {
  id: "ecuador-provinces",
  name: "Provinces",
  description: ECUADOR_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: ECUADOR_PROVINCE_QUESTIONS,
};
