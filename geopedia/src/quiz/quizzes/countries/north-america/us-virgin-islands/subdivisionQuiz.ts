/**
 * Quiz configuration for the U.S. Virgin Islands' subdivisions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  US_VIRGIN_ISLANDS_ISLANDS_BY_ID,
  US_VIRGIN_ISLANDS_SUBDIVISION_QUESTIONS,
} from "./data/admin";

const US_VIRGIN_ISLANDS_SUBDIVISIONS_DESCRIPTION = `
  Learn all ${US_VIRGIN_ISLANDS_SUBDIVISION_QUESTIONS.length} subdivisions
  of the U.S. Virgin Islands, with filters that let you practice subdivisions
  by island.
`;

export const usVirginIslandsSubdivisionsQuiz: FeatureQuiz = {
  id: "us-virgin-islands-subdivisions",
  name: "Subdivisions",
  description: US_VIRGIN_ISLANDS_SUBDIVISIONS_DESCRIPTION,

  kind: "feature",
  mapId: "us-virgin-islands-subdivisions",

  answerProperty: "subdivision_id",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "island_id",
        label: "Island",
        valueType: "string",
        valueLabels: US_VIRGIN_ISLANDS_ISLANDS_BY_ID,
      },
    ],
  },

  questions: US_VIRGIN_ISLANDS_SUBDIVISION_QUESTIONS,
};
