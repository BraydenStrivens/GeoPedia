/**
 * Feature quiz for Tunisia's wilayat (governorates).
 *
 * Governorates can be grouped by Tunisia's six broad administrative regions.
 * Question labels include both source and Arabic-native display forms.
 */

import type { FeatureQuiz, FeatureQuizQuestion } from "@/types/quiz";

import { TUNISIA_GOVERNORATES_BY_ID } from "./data/admin";

const TUNISIA_GOVERNORATE_QUESTIONS: FeatureQuizQuestion[] =
  Object.entries(TUNISIA_GOVERNORATES_BY_ID).map(
    ([governorateId, governorate]) => ({
      answer: governorateId,
      display: governorate.display,
      nativeDisplay: governorate.nativeDisplay,
    }),
  );

const DESCRIPTION =
  `Learn all ${TUNISIA_GOVERNORATE_QUESTIONS.length} wilayat (governorates) ` +
  `of Tunisia. They can be grouped by region for more focused practice.`;

export const tunisiaGovernoratesQuiz: FeatureQuiz = {
  id: "tunisia-governorates",
  name: "Wilayat (Governorates)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "tunisia-governorates",

  answerProperty: "governorate_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region_id",
        label: "Region",
        valueType: "string",
        valueLabels: Object.fromEntries(
          Object.values(TUNISIA_GOVERNORATES_BY_ID).map(
            (governorate) => [
              governorate.regionId,
              governorate.region,
            ],
          ),
        ),
      },
    ],
  },

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: TUNISIA_GOVERNORATE_QUESTIONS,
};
