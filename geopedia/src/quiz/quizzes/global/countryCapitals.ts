/**
 * Tests recognition of countries from their capitals.
 *
 * Each question displays a capital and expects the user to select the country
 * to which that capital belongs.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COUNTRY_CAPITAL_QUESTIONS } from "./data/countryCapitals";

const COUNTRY_CAPITALS_DESCRIPTION =
  `Identify all ${COUNTRY_CAPITAL_QUESTIONS.length} countries by their capitals, with filters ` +
  `for GeoGuessr countries only, continent, region, and subregion.`;

export const countryCapitalsQuiz: FeatureQuiz = {
  id: "country-capitals",
  name: "Country Capitals",
  description: COUNTRY_CAPITALS_DESCRIPTION,

  kind: "feature",
  mapId: "world-countries",

  answerProperty: "iso_a3",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
    townLabels: false,
  },

  grouping: {
    properties: [
      {
        property: "continent",
        label: "Continent",
        valueType: "string",
      },
      {
        property: "region",
        label: "Region",
        valueType: "string",
      },
      {
        property: "subregion",
        label: "Subregion",
        valueType: "string",
      },
    ],
  },

  questions: COUNTRY_CAPITAL_QUESTIONS,
};
