/**
 * Quiz configuration for Ecuador's third-level administrative parishes.
 *
 * Questions can be grouped by province or canton for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ECUADOR_PARISHES_BY_ID } from "./data/admin";

const ECUADOR_PARISH_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(ECUADOR_PARISHES_BY_ID).map(
    ([parishId, parish]) => ({
      answer: parishId,
      display: parish.name,
    }),
  );

const ECUADOR_PARISHES_DESCRIPTION =
  `Learn all ${ECUADOR_PARISH_QUESTIONS.length} parishes of Ecuador and ` +
  `where they are located across the country. Use the Province or Canton ` +
  `groupings to break the full quiz into smaller areas.`;

export const ecuadorParishesQuiz: FeatureQuiz = {
  id: "ecuador-parishes",
  name: "Parishes",
  description: ECUADOR_PARISHES_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-parishes",

  answerProperty: "parish_id",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province",
        valueType: "string",
      },
      {
        property: "canton",
        label: "Canton",
        valueType: "string",
      },
    ],
  },

  questions: ECUADOR_PARISH_QUESTIONS,
};
