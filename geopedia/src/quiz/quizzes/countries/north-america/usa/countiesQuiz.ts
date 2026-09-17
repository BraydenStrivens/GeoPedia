/**
 * Quiz for identifying United States counties and county equivalents.
 *
 * County answers use Census GEOIDs and duplicate county names are
 * disambiguated by their state or territory.
 */

import type { FeatureQuiz } from "@/types/quiz";

import {
  US_COUNTIES_BY_ID,
  US_SUBDIVISION_BY_ABBREVIATION,
} from "./data/admin";

const US_COUNTY_QUESTIONS: FeatureQuiz["questions"] = Object.entries(
  US_COUNTIES_BY_ID,
).map(([id, countyData]) => ({
  answer: id,
  display: countyData.name,
}));

const US_COUNTIES_DESCRIPTION =
  `Learn all ${US_COUNTY_QUESTIONS.length} U.S. counties, including U.S. ` +
  `territories, with filtering options to practice any desired subset.`;

export const usCountiesQuiz: FeatureQuiz = {
  id: "us-counties",
  name: "Counties",
  description: US_COUNTIES_DESCRIPTION,

  mapId: "us-counties",
  kind: "feature",

  answerProperty: "geoid",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "state",
        label: "State",
        valueType: "string",
        valueLabels: US_SUBDIVISION_BY_ABBREVIATION,
      },
    ],
  },

  questions: US_COUNTY_QUESTIONS,
};
