/**
 * Quiz configuration for Ecuador's second-level administrative cantons.
 *
 * Questions can be grouped by province for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { ECUADOR_CANTONS_BY_ID } from "./data/admin";

const ECUADOR_CANTON_QUESTIONS: FeatureQuiz["questions"] =
  Object.entries(ECUADOR_CANTONS_BY_ID).map(([cantonId, canton]) => ({
    answer: cantonId,
    display: canton.name,
  }));

const ECUADOR_CANTONS_DESCRIPTION =
  `Learn all ${ECUADOR_CANTON_QUESTIONS.length} cantons of Ecuador and ` +
  `where they are located across the country. Use the Province grouping to ` +
  `learn the cantons one province at a time.`;

export const ecuadorCantonsQuiz: FeatureQuiz = {
  id: "ecuador-cantons",
  name: "Cantons",
  description: ECUADOR_CANTONS_DESCRIPTION,

  kind: "feature",
  mapId: "ecuador-cantons",

  answerProperty: "canton_id",
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

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: ECUADOR_CANTON_QUESTIONS,
};
