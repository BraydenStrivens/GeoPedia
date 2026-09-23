/**
 * Feature quiz for Rwanda's imirenge (sectors), grouped by province and
 * district.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { RWANDA_SECTORS_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${RWANDA_SECTORS_QUIZ_QUESTIONS.length} imirenge (sectors) ` +
  `of Rwanda.`;

export const rwandaSectorsQuiz: FeatureQuiz = {
  id: "rwanda-sectors",
  name: "Imirenge (Sectors)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "rwanda-sectors",

  answerProperty: "sector_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "district",
        label: "District",
        valueType: "string",
      },
    ],
  },

  questions: RWANDA_SECTORS_QUIZ_QUESTIONS,
};
