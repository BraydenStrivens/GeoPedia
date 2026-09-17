/**
 * Global map quiz that displays a country flag and asks the player to select
 * its corresponding geographic feature on the world map.
 *
 * Quiz answers intentionally preserve the raw `iso_a3` values stored by
 * world-countries.geojson because that same property is used by the map's
 * feature interactions.
 */

import type { FeatureQuiz } from "@/types/quiz";

import { COUNTRY_NAME_QUESTIONS } from "./data/countryNames";

const COUNTRY_FLAG_QUESTIONS: FeatureQuiz["questions"] =
  COUNTRY_NAME_QUESTIONS.map((country) => ({
    answer: country.answer,
    display: country.display,
    prompt: {
      type: "image",
      imageUrl: `/data/global/countries/flags/${country.answer.toLowerCase()}.svg`,
      alt: `${country.display} Flag`,
    },
  }));

const COUNTRY_FLAGS_DESCRIPTION =
  `Identify all ${COUNTRY_FLAG_QUESTIONS.length} countries by their flags, with filters ` +
  `for GeoGuessr countries only, continent, region, and subregion.`;

export const countryFlagsQuiz: FeatureQuiz = {
  id: "country-flags",
  name: "Country Flags",
  description: COUNTRY_FLAGS_DESCRIPTION,

  mapId: "world-countries",
  kind: "feature",

  answerProperty: "iso_a3",
  answerType: "single",

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

  questions: COUNTRY_FLAG_QUESTIONS,
};
