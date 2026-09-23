/**
 * Feature quiz for Uganda's districts.
 *
 * Districts can be grouped by their parent region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { UGANDA_DISTRICTS_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION = `Learn all ${UGANDA_DISTRICTS_QUIZ_QUESTIONS.length} districts of Uganda.`;

export const ugandaDistrictsQuiz: FeatureQuiz = {
  id: "uganda-districts",
  name: "Districts",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "uganda-districts",

  answerProperty: "district_id",
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

  questions: UGANDA_DISTRICTS_QUIZ_QUESTIONS,
};
