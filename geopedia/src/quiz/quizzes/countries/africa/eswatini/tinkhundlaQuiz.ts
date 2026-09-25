/**
 * Feature quiz for Eswatini's tinkhundla (constituencies).
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ESWATINI_TINKHUNDLA_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn the ${ESWATINI_TINKHUNDLA_QUIZ_QUESTIONS.length} tinkhundla (constituencies) of Eswatini. ` +
  `Group the tinkhundla (constituencies) by region to learn the country in smaller sections.`;

export const eswatiniTinkhundlaQuiz: FeatureQuiz = {
  id: "eswatini-tinkhundla",
  name: "Tinkhundla (Constituencies)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "eswatini-tinkhundla",

  answerProperty: "inkhundla_id",
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

  questions: ESWATINI_TINKHUNDLA_QUIZ_QUESTIONS,
};
