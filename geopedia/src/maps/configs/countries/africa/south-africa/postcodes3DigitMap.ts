/**
 * Map configuration for South Africa's three-digit postcode-prefix quiz.
 *
 * The geography is derived by dissolving the reconstructed four-digit
 * postcode map so the two quiz levels remain spatially consistent.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaPostcodes3DigitMap = createMapConfig({
  id: "south-africa-postcodes-3",
  geojsonUrl:
    "/data/countries/south-africa/geojson/postcodes-3.geojson",
  featureProperty: "prefix_3",
  promoteId: "prefix_3",
  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 75,
    labelsPerZoom: 125,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "prefix_3",
  },
});
