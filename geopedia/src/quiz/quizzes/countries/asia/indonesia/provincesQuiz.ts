/**
 * Quiz configuration for Indonesia's first-level administrative provinces.
 *
 * Provinces can be grouped by major geographic region for focused practice.
 */

import { FeatureQuiz } from "@/types/quiz";

import { INDONESIA_PROVINCE_QUESTIONS } from "./data/admin";

const INDONESIA_PROVINCES_DESCRIPTION =
  `Learn all ${INDONESIA_PROVINCE_QUESTIONS.length} provinsi (provinces) of ` +
  `Indonesia. Provinces can be grouped by region for more focused practice.`;

export const indonesiaProvincesQuiz: FeatureQuiz = {
  id: "indonesia-provinces",
  name: "Provinsi (Provinces)",
  description: INDONESIA_PROVINCES_DESCRIPTION,

  kind: "feature",
  quizTopic: "Administrative Regions",
  mapId: "indonesia-provinces",

  answerProperty: "province_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: INDONESIA_PROVINCE_QUESTIONS,
};
