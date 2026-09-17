/**
 * Quiz configuration for the U.S. Virgin Islands' islands.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { US_VIRGIN_ISLANDS_ISLANDS_BY_ID } from "./data/admin";

const US_VIRGIN_ISLANDS_ISLAND_QUESTIONS = Object.entries(
  US_VIRGIN_ISLANDS_ISLANDS_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

const US_VIRGIN_ISLANDS_ISLANDS_DESCRIPTION = `
  Learn all ${US_VIRGIN_ISLANDS_ISLAND_QUESTIONS.length} main islands
  of the U.S. Virgin Islands.
`;

export const usVirginIslandsIslandsQuiz: FeatureQuiz = {
  id: "us-virgin-islands-islands",
  name: "Islands",
  description: US_VIRGIN_ISLANDS_ISLANDS_DESCRIPTION,

  kind: "feature",
  mapId: "us-virgin-islands-islands",

  answerProperty: "island_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: US_VIRGIN_ISLANDS_ISLAND_QUESTIONS,
};
