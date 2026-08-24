/**
 * Defines the United States state abbreviations quiz.
 *
 * This quiz uses the shared US states map and asks the user to identify
 * states by their two-letter postal abbreviations. The `answerProperty`
 * connects each quiz answer to the corresponding `abbreviation` property
 * in the US states GeoJSON data.
 */

import type { Quiz } from "@/types/quiz";

/**
 * Quiz definition for identifying US states by postal abbreviation.
 */
export const usStateAbbreviationsQuiz: Quiz = {
  id: "us-state-abbreviations",
  name: "US State Abbreviations",
  mapId: "us-states",
  answerProperty: "abbreviation",
  answerType: "single",

  grouping: {
    properties: [
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
    ],
  },

  questions: [
    { answer: "AL" },
    { answer: "AK" },
    { answer: "AZ" },
    { answer: "AR" },
    { answer: "CA" },
    { answer: "CO" },
    { answer: "CT" },
    { answer: "DE" },
    { answer: "FL" },
    { answer: "GA" },
    { answer: "HI" },
    { answer: "ID" },
    { answer: "IL" },
    { answer: "IN" },
    { answer: "IA" },
    { answer: "KS" },
    { answer: "KY" },
    { answer: "LA" },
    { answer: "ME" },
    { answer: "MD" },
    { answer: "MA" },
    { answer: "MI" },
    { answer: "MN" },
    { answer: "MS" },
    { answer: "MO" },
    { answer: "MT" },
    { answer: "NE" },
    { answer: "NV" },
    { answer: "NH" },
    { answer: "NJ" },
    { answer: "NM" },
    { answer: "NY" },
    { answer: "NC" },
    { answer: "ND" },
    { answer: "OH" },
    { answer: "OK" },
    { answer: "OR" },
    { answer: "PA" },
    { answer: "RI" },
    { answer: "SC" },
    { answer: "SD" },
    { answer: "TN" },
    { answer: "TX" },
    { answer: "UT" },
    { answer: "VT" },
    { answer: "VA" },
    { answer: "WA" },
    { answer: "WV" },
    { answer: "WI" },
    { answer: "WY" },
  ],
};
