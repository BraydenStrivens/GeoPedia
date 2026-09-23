/**
 * Feature quiz for Rwanda's utugali (cells), grouped through the
 * administrative hierarchy from province to sector.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { RWANDA_CELLS_QUIZ_QUESTIONS } from "./data/admin";

const DESCRIPTION =
  `Learn all ${RWANDA_CELLS_QUIZ_QUESTIONS.length} utugali (cells) ` +
  `of Rwanda.`;

export const rwandaCellsQuiz: FeatureQuiz = {
  id: "rwanda-cells",
  name: "Utugali (Cells)",
  description: DESCRIPTION,

  kind: "feature",
  mapId: "rwanda-cells",

  answerProperty: "cell_id",
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
      {
        property: "sector",
        label: "Sector",
        valueType: "string",
      },
    ],
  },

  questions: RWANDA_CELLS_QUIZ_QUESTIONS,
};
