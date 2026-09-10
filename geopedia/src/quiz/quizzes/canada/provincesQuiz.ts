/**
 * Defines the Canada provinces and territories quiz.
 *
 * This quiz uses the shared Canada provinces map and asks the user to identify
 * all 10 provinces and 3 territories by name. Each quiz answer corresponds to
 * the `name` property in the processed Canada province and territory GeoJSON
 * dataset.
 *
 * No grouping is defined because the quiz contains only 13 questions, making
 * the full set small enough to practice comfortably without predefined groups.
 */

import type { FeatureQuiz } from "@/types/quiz";

const CANADA_PROVINCE_QUESTIONS: FeatureQuiz["questions"] = [
  { answer: "Newfoundland and Labrador" },
  { answer: "Prince Edward Island" },
  { answer: "Nova Scotia" },
  { answer: "New Brunswick" },
  { answer: "Quebec" },
  { answer: "Ontario" },
  { answer: "Manitoba" },
  { answer: "Saskatchewan" },
  { answer: "Alberta" },
  { answer: "British Columbia" },
  { answer: "Yukon" },
  { answer: "Northwest Territories" },
  { answer: "Nunavut" },
];

const CANADA_PROVINCES_DESCRIPTION = `Learn all ${CANADA_PROVINCE_QUESTIONS.length} Canadian provinces and territories by their location on the map.`;

/**
 * Quiz definition for identifying Canadian provinces and territories by name.
 */
export const canadaProvincesQuiz: FeatureQuiz = {
  id: "canada-provinces",
  name: "Provinces and Territories",
  description: CANADA_PROVINCES_DESCRIPTION,

  kind: "feature",
  mapId: "canada-provinces",

  answerProperty: "name",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  questions: CANADA_PROVINCE_QUESTIONS,
};
