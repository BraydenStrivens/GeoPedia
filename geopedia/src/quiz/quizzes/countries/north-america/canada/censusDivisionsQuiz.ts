/**
 * Quiz configuration for Canada's census divisions.
 *
 * Census Division Unique Identifiers (CDUIDs) are used as answer values so
 * divisions remain uniquely identifiable. Questions can be grouped by
 * province or territory for more focused practice.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { CANADA_CENSUS_DIVISION_QUESTIONS } from "./data/censusDivisions";

const CANADA_CENSUS_DIVISIONS_DESCRIPTION =
  `Learn ${CANADA_CENSUS_DIVISION_QUESTIONS.length} census divisions across Canada, ` +
  `including counties, regional districts, regional county municipalities, ` +
  `and other county-equivalent statistical regions.`;

export const canadaCensusDivisionsQuiz: FeatureQuiz = {
  id: "canada-census-divisions",
  name: "Census Divisions",
  description: CANADA_CENSUS_DIVISIONS_DESCRIPTION,

  kind: "feature",
  mapId: "canada-census-divisions",

  answerProperty: "cduid",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "province",
        label: "Province / Territory",
        valueType: "string",
      },
    ],
  },

  questions: CANADA_CENSUS_DIVISION_QUESTIONS,
};
