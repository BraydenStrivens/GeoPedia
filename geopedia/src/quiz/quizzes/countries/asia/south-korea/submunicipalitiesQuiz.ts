/**
 * Feature quiz for South Korea's 3,504 submunicipalities.
 *
 * Questions use each submunicipality's stable canonical ID as the answer.
 * Duplicate romanized Korean and Korean names use independently generated
 * hierarchy-aware displays. Submunicipalities can be grouped by province or
 * municipality.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { SOUTH_KOREA_SUBMUNICIPALITIES_BY_ID } from "./data/admin";

const QUESTIONS: FeatureQuizQuestion[] = Object.entries(
  SOUTH_KOREA_SUBMUNICIPALITIES_BY_ID,
).map(([submunicipalityId, submunicipality]) => ({
  answer: submunicipalityId,
  display: submunicipality.display,
  nativeDisplay: submunicipality.nativeDisplay,
}));

const DESCRIPTION =
  `Learn all ${QUESTIONS.length} submunicipalities of South Korea. ` +
  `Use province and municipality groups to study them in smaller regional sets. ` +
  `In Korean submunicipality names, administrative types usually appear as suffixes: ` +
  `eup (읍) means town, myeon (면) means township, and dong (동) means neighborhood.`;

export const southKoreaSubmunicipalitiesQuiz: FeatureQuiz = {
  id: "south-korea-submunicipalities",
  name: "읍·면·동 (Eup · Myeon · Dong) (Submunicipalities)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "south-korea-submunicipalities",

  answerProperty: "submunicipality_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "municipality",
        label: "Municipality",
        valueType: "string",
      },
    ],
  },

  questions: QUESTIONS,
};
