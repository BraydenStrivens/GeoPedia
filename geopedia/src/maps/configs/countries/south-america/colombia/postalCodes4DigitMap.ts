/**
 * Map configuration for Colombia's 4-digit postal-code regions.
 *
 * These regions represent the first four digits of Colombia's 6-digit
 * postal codes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { COLOMBIA_INITIAL_VIEW } from "./constants";

export const colombiaPostalCodes4DigitMap = createMapConfig({
  id: "colombia-postal-codes-4-digit",

  geojsonUrl:
    "/data/countries/colombia/geojson/postal-codes-4-digit.geojson",

  featureProperty: "postal_code_4_digit",
  promoteId: "id",

  answerLabels: {
    densityThreshold: 250,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: COLOMBIA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "postal_code_4_digit",
  },
});
