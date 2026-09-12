import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Colombia's 4-digit postal-code regions.
 */
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

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-74.3, 4.5],
    zoom: 4.6,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "postal_code_4_digit",
  },
});
