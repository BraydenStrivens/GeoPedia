/**
 * Map configuration for South Africa's one-digit postcode-prefix quiz.
 *
 * This is the broadest South African postcode quiz and is derived from the
 * same reconstructed four-digit postcode geography as the finer levels.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaPostcodes1DigitMap = createMapConfig({
  id: "south-africa-postcodes-1",
  geojsonUrl:
    "/data/countries/south-africa/geojson/postcodes-1.geojson",
  featureProperty: "prefix_1",
  promoteId: "prefix_1",
  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 50,
    initialMaxLabels: 10,
    labelsPerZoom: 10,
  },

  layers: {
    borders: {
      width: 1.25,
    },
  },

  hover: {
    labelProperty: "prefix_1",
  },
});
