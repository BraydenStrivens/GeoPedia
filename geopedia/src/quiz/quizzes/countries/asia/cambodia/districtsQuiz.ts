/**
 * Quiz configuration for Cambodia's second-level administrative divisions.
 *
 * Districts can be grouped by their parent province for focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CAMBODIA_DISTRICT_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${CAMBODIA_DISTRICT_QUESTIONS.length.toLocaleString()} second-level ` +
  `administrative divisions of Cambodia. These include ស្រុក (Srok) districts, ` +
  `ក្រុង (Krong) municipalities, and ខណ្ឌ (Khan) urban districts, and can be grouped by province.`;

export const cambodiaDistrictsQuiz: FeatureQuiz = {
  id: "cambodia-districts",
  name: "ស្រុក · ក្រុង · ខណ្ឌ - Srok · Krong · Khan (Districts)",
  description: DESCRIPTION,

  quizTopic: "Administrative Regions",
  kind: "feature",
  mapId: "cambodia-districts",

  answerProperty: "district_id",
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

  questions: CAMBODIA_DISTRICT_QUESTIONS,
};
