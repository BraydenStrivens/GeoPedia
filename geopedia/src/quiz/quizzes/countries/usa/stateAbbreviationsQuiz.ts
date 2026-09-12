import type { FeatureQuiz } from "@/types/quiz";

/**
 * Postal abbreviations for the 50 U.S. states.
 *
 * The District of Columbia and U.S. territories are intentionally excluded.
 */
export const US_STATE_ABBREVIATIONS = [
  "AL",
  "AK",
  "AZ",
  "AR",
  "CA",
  "CO",
  "CT",
  "DE",
  "FL",
  "GA",
  "HI",
  "ID",
  "IL",
  "IN",
  "IA",
  "KS",
  "KY",
  "LA",
  "ME",
  "MD",
  "MA",
  "MI",
  "MN",
  "MS",
  "MO",
  "MT",
  "NE",
  "NV",
  "NH",
  "NJ",
  "NM",
  "NY",
  "NC",
  "ND",
  "OH",
  "OK",
  "OR",
  "PA",
  "RI",
  "SC",
  "SD",
  "TN",
  "TX",
  "UT",
  "VT",
  "VA",
  "WA",
  "WV",
  "WI",
  "WY",
] as const;

/**
 * Questions for the U.S. state abbreviations quiz.
 */
const US_STATE_ABBREVIATION_QUESTIONS: FeatureQuiz["questions"] =
  US_STATE_ABBREVIATIONS.map((answer) => ({
    answer,
  }));

/**
 * User-facing description for the U.S. state abbreviations quiz.
 */
const US_STATE_ABBREVIATION_DESCRIPTION =
  `Learn the abbreviations for all ${US_STATE_ABBREVIATION_QUESTIONS.length} ` +
  `U.S. states. This quiz includes the 50 states only and does not include ` +
  `U.S. territories.`;

/**
 * Quiz definition for identifying U.S. states by postal abbreviation.
 */
export const usStateAbbreviationsQuiz: FeatureQuiz = {
  id: "us-state-abbreviations",
  name: "State Abbreviations",
  description: US_STATE_ABBREVIATION_DESCRIPTION,

  mapId: "us-states",
  kind: "feature",

  answerProperty: "abbreviation",
  answerType: "single",

  baseMapLayers: {
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

  questions: US_STATE_ABBREVIATION_QUESTIONS,
};
