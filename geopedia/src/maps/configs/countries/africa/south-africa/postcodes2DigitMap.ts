/**
 * Map configuration for South Africa's two-digit postcode-prefix quiz.
 *
 * The geography is derived from the reconstructed four-digit postcode base
 * so postcode-prefix boundaries remain consistent across quiz levels.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaPostcodes2DigitMap = createMapConfig({
  id: "south-africa-postcodes-2",
  geojsonUrl:
    "/data/countries/south-africa/geojson/postcodes-2.geojson",
  featureProperty: "prefix_2",
  promoteId: "prefix_2",
  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 150,
    initialMaxLabels: 98,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "prefix_2",
  },
});
