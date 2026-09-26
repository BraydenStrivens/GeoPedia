/**
 * Feature quiz for Japan's 9 regions.
 *
 * Questions use each region's stable canonical ID as the answer and provide
 * both English and Japanese player-facing names.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { JAPAN_REGIONS_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  JAPAN_REGIONS_BY_ID,
).map(([regionId, region]) => ({
  answer: regionId,
  display: region.name,
  nativeDisplay: region.nativeName,
}));

const DESCRIPTION = `Learn all ${QUESTIONS.length} regions of Japan.`;

export const japanRegionsQuiz: FeatureQuiz = {
  id: "japan-regions",
  name: "地方 (Chihō) (Regions)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "japan-regions",

  answerProperty: "region_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
    subdivisionLabels: false,
  },

  questions: QUESTIONS,
};
