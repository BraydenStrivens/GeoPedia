/**
 * Feature quiz configuration for Namibia's 107 constituencies.
 *
 * Constituency pcodes provide stable answer identity. Manual and custom quiz
 * groups can be created from each constituency's parent region.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { NAMIBIA_CONSTITUENCIES_QUIZ_QUESTIONS } from "./data/admin";

const NAMIBIA_CONSTITUENCIES_DESCRIPTION = `Learn all ${NAMIBIA_CONSTITUENCIES_QUIZ_QUESTIONS.length} constituencies of Namibia.`;

export const namibiaConstituenciesQuiz: FeatureQuiz = {
  id: "namibia-constituencies",
  name: "Constituencies",
  description: NAMIBIA_CONSTITUENCIES_DESCRIPTION,

  kind: "feature",
  mapId: "namibia-constituencies",

  answerProperty: "constituency_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionBorders: false,
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: NAMIBIA_CONSTITUENCIES_QUIZ_QUESTIONS,
};
