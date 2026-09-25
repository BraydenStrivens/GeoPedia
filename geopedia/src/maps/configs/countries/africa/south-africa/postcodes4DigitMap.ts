/**
 * Map configuration for South Africa's four-digit postcode quiz.
 *
 * Uses reconstructed postcode polygons derived from cleaned OSM postcode
 * observations. This is the highest-resolution South African postcode map.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaPostcodes4DigitMap = createMapConfig({
  id: "south-africa-postcodes-4",
  geojsonUrl:
    "/data/countries/south-africa/geojson/postcodes-4.geojson",
  featureProperty: "postcode",
  promoteId: "postcode",
  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 250,
    initialMaxLabels: 50,
    labelsPerZoom: 100,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "postcode",
  },
});
