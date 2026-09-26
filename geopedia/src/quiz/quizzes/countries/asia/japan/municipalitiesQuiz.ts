/**
 * Feature quiz for Japan's 1,892 municipalities.
 *
 * Questions use each municipality's stable canonical ID as the answer.
 * Duplicate English and Japanese names use independently generated
 * hierarchy-aware displays. Municipalities can be grouped by prefecture
 * or region.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { JAPAN_MUNICIPALITIES_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  JAPAN_MUNICIPALITIES_BY_ID,
).map(([municipalityId, municipality]) => ({
  answer: municipalityId,
  display: municipality.display,
  nativeDisplay: municipality.nativeDisplay,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} municipalities of Japan. ` +
  `Use prefecture and region groups to study them in smaller regional sets.`;

export const japanMunicipalitiesQuiz: FeatureQuiz = {
  id: "japan-municipalities",
  name: "自治体 (Jichitai) (Municipalities)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "japan-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "prefecture",
        label: "Prefecture",
        valueType: "string",
      },
    ],
  },

  questions: QUESTIONS,
};
