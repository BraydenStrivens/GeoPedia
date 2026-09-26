/**
 * Feature quiz for South Korea's 250 municipalities.
 *
 * Questions use each municipality's stable canonical ID as the answer.
 * Duplicate romanized Korean and Korean names use independently generated
 * hierarchy-aware displays. Municipalities can be grouped by province.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { SOUTH_KOREA_MUNICIPALITIES_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  SOUTH_KOREA_MUNICIPALITIES_BY_ID,
).map(([municipalityId, municipality]) => ({
  answer: municipalityId,
  display: municipality.display,
  nativeDisplay: municipality.nativeDisplay,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} municipalities of South Korea. ` +
  `Use province groups to study them in smaller regional sets. ` +
  `In Korean municipality names, administrative types usually appear as suffixes: ` +
  `si (시) means city, gun (군) means county, and gu (구) means district.`;

export const southKoreaMunicipalitiesQuiz: FeatureQuiz = {
  id: "south-korea-municipalities",
  name: "시·군·구 (Si · Gun · Gu) (Municipalities)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-korea-municipalities",

  answerProperty: "municipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
    ],
  },

  questions: QUESTIONS,
};
