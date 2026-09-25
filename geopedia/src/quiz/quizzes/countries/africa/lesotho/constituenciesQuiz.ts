/**
 * Feature quiz for Lesotho's 78 constituencies.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { LESOTHO_CONSTITUENCY_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn the ${LESOTHO_CONSTITUENCY_QUIZ_QUESTIONS.length} constituencies of Lesotho. ` +
  `Group the constituencies by district to learn the country in smaller sections.`;

export const lesothoConstituenciesQuiz: FeatureQuiz = {
  id: "lesotho-constituencies",
  name: "Constituencies",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "lesotho-constituencies",

  answerProperty: "constituency_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
    ],
  },

  questions: LESOTHO_CONSTITUENCY_QUIZ_QUESTIONS,
};
