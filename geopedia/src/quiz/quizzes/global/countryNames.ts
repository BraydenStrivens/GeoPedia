/**
 * Tests recognition of countries by name on GeoPedia's global country map.
 *
 * Each question displays a country name and expects the user to select the
 * corresponding geographic country. Countries with distinct native/local
 * names can be displayed in either English or Native question language.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COUNTRY_NAME_QUESTIONS } from "./data/countryNames";

const COUNTRY_NAMES_DESCRIPTION =
  `Identify all ${COUNTRY_NAME_QUESTIONS.length} countries by their names on the map. ` +
  `Choose English or Native names, with multiple locally used names separated by " / " where applicable. ` +
  `Filter by GeoGuessr countries only, continent, region, and subregion.`;

export const countryNamesQuiz: FeatureQuiz = {
  id: "country-names",
  name: "Country Names",
  description: COUNTRY_NAMES_DESCRIPTION,

  mapId: "world-countries",
  kind: "feature",

  answerProperty: "iso_a3",
  answerType: "single",

  baseMapLayers: {
    subdivisionLabels: false,
    countryLabels: false,
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

  questions: COUNTRY_NAME_QUESTIONS,
};
