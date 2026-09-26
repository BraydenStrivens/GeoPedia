/**
 * Feature quiz for Japan's 47 prefectures.
 *
 * Questions use each prefecture's stable canonical ID as the answer and
 * provide both English and Japanese player-facing names. Prefectures can be
 * grouped by region.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { JAPAN_PREFECTURES_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  JAPAN_PREFECTURES_BY_ID,
).map(([prefectureId, prefecture]) => ({
  answer: prefectureId,
  display: prefecture.name,
  nativeDisplay: prefecture.nativeName,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} prefectures of Japan. ` +
  `Use region groups to study them in smaller regional sets.`;

export const japanPrefecturesQuiz: FeatureQuiz = {
  id: "japan-prefectures",
  name: "府県 (Fuken) (Prefectures)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "japan-prefectures",

  answerProperty: "prefecture_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: QUESTIONS,
};
