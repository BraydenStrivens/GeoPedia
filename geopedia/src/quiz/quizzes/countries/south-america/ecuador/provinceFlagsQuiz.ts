/**
 * Quiz configuration for identifying Ecuador's provinces from their flags.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ECUADOR_PROVINCE_FLAG_QUESTIONS } from "./data/provinceFlags";

const ECUADOR_PROVINCE_FLAGS_DESCRIPTION =
  `Learn the flags of all ${ECUADOR_PROVINCE_FLAG_QUESTIONS.length} provinces ` +
  `of Ecuador by identifying the corresponding province on the map.`;

export const ecuadorProvinceFlagsQuiz: FeatureQuiz = {
  id: "ecuador-province-flags",
  name: "Province Flags",
  description: ECUADOR_PROVINCE_FLAGS_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-provinces",

  answerProperty: "province_id",
  answerType: "single",

  questions: ECUADOR_PROVINCE_FLAG_QUESTIONS,
};
