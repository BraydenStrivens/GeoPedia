/**
 * Feature quiz for Rwanda's uturere (districts), grouped by province.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { RWANDA_DISTRICTS_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${RWANDA_DISTRICTS_QUIZ_QUESTIONS.length} uturere (districts) ` +
  `of Rwanda.`;

export const rwandaDistrictsQuiz: FeatureQuiz = {
  id: "rwanda-districts",
  name: "Uturere (Districts)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "rwanda-districts",

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

  questions: RWANDA_DISTRICTS_QUIZ_QUESTIONS,
};
