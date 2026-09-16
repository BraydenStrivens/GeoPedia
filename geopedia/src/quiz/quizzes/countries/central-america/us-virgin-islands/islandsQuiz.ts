import type { FeatureQuiz } from "@/types/quiz";

/**
 * U.S. Virgin Islands island names keyed by Census county-equivalent GEOID.
 */
export const US_VIRGIN_ISLANDS_ISLAND_NAMES_BY_ID = {
  "78010": "St. Croix",
  "78020": "St. John",
  "78030": "St. Thomas",
};

/**
 * Questions for the U.S. Virgin Islands islands quiz.
 */
const US_VIRGIN_ISLANDS_ISLAND_QUESTIONS = Object.entries(
  US_VIRGIN_ISLANDS_ISLAND_NAMES_BY_ID,
).map(([answer, display]) => ({
  answer,
  display,
}));

/**
 * Quiz configuration for the U.S. Virgin Islands' islands.
 */
export const usVirginIslandsIslandsQuiz: FeatureQuiz = {
  id: "us-virgin-islands-islands",
  name: "Islands",
  description: `Learn all ${US_VIRGIN_ISLANDS_ISLAND_QUESTIONS.length} main islands of the U.S. Virgin Islands.`,

  kind: "feature",
  mapId: "us-virgin-islands-islands",

  answerProperty: "island_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: US_VIRGIN_ISLANDS_ISLAND_QUESTIONS,
};
