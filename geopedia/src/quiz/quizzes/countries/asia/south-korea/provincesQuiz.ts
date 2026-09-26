/**
 * Feature quiz for South Korea's 17 provinces.
 *
 * Questions use each province's stable canonical ID as the answer and provide
 * both romanized Korean and Korean player-facing names.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { SOUTH_KOREA_PROVINCES_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  SOUTH_KOREA_PROVINCES_BY_ID,
).map(([provinceId, province]) => ({
  answer: provinceId,
  display: province.name,
  nativeDisplay: province.nativeName,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} provinces of South Korea. ` +
  `In Korean province names, -do (도) means province. Directional words usually ` +
  `appear as suffixes: buk (북) means north, nam (남) means south, ` +
  `dong (동) means east, and seo (서) means west.`;

export const southKoreaProvincesQuiz: FeatureQuiz = {
  id: "south-korea-provinces",
  name: "도 (Do) (Provinces)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-korea-provinces",

  answerProperty: "province_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
    subdivisionLabels: false,
  },

  questions: QUESTIONS,
};
