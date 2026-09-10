import type { FeatureQuiz } from "@/types/quiz";

import { US_STATE_ABBREVIATIONS } from "./stateAbbreviationsQuiz";

/**
 * Maps U.S. postal abbreviations to their full subdivision names.
 *
 * Includes the 50 states, the District of Columbia, and U.S. territories
 * represented by standard postal abbreviations.
 */
export const US_SUBDIVISION_NAMES_BY_ABBREVIATION = {
  AL: "Alabama",
  AK: "Alaska",
  AZ: "Arizona",
  AR: "Arkansas",
  CA: "California",
  CO: "Colorado",
  CT: "Connecticut",
  DE: "Delaware",
  FL: "Florida",
  GA: "Georgia",
  HI: "Hawaii",
  ID: "Idaho",
  IL: "Illinois",
  IN: "Indiana",
  IA: "Iowa",
  KS: "Kansas",
  KY: "Kentucky",
  LA: "Louisiana",
  ME: "Maine",
  MD: "Maryland",
  MA: "Massachusetts",
  MI: "Michigan",
  MN: "Minnesota",
  MS: "Mississippi",
  MO: "Missouri",
  MT: "Montana",
  NE: "Nebraska",
  NV: "Nevada",
  NH: "New Hampshire",
  NJ: "New Jersey",
  NM: "New Mexico",
  NY: "New York",
  NC: "North Carolina",
  ND: "North Dakota",
  OH: "Ohio",
  OK: "Oklahoma",
  OR: "Oregon",
  PA: "Pennsylvania",
  RI: "Rhode Island",
  SC: "South Carolina",
  SD: "South Dakota",
  TN: "Tennessee",
  TX: "Texas",
  UT: "Utah",
  VT: "Vermont",
  VA: "Virginia",
  WA: "Washington",
  WV: "West Virginia",
  WI: "Wisconsin",
  WY: "Wyoming",

  AS: "American Samoa",
  DC: "District of Columbia",
  GU: "Guam",
  MP: "Northern Mariana Islands",
  PR: "Puerto Rico",
  VI: "U.S. Virgin Islands",
} as const;

/**
 * Questions for the U.S. states quiz.
 */
const US_STATE_QUESTIONS: FeatureQuiz["questions"] =
  US_STATE_ABBREVIATIONS.map((abbreviation) => ({
    answer: US_SUBDIVISION_NAMES_BY_ABBREVIATION[abbreviation],
  }));

/**
 * User-facing description for the U.S. states quiz.
 */
const US_STATES_DESCRIPTION =
  `Learn all ${US_STATE_QUESTIONS.length} U.S. states by their location on the ` +
  `map. This quiz includes the 50 states only and does not include U.S. ` +
  `territories.`;

/**
 * Quiz definition for identifying U.S. states by name.
 */
export const usStatesQuiz: FeatureQuiz = {
  id: "us-states",
  name: "States",
  description: US_STATES_DESCRIPTION,

  kind: "feature",
  mapId: "us-states",

  answerProperty: "name",
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

  questions: US_STATE_QUESTIONS,
};
