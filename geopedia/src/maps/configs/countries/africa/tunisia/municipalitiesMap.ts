/**
 * Map configuration for Tunisia's baladiyat (municipalities).
 *
 * Municipality maps use reduced border width and aggressive answer-label
 * throttling because Tunisia contains more than 2,000 small geographic
 * features.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TUNISIA_INITIAL_VIEW } from "./constants";

export const tunisiaMunicipalitiesMap = createMapConfig({
  id: "tunisia-municipalities",

  geojsonUrl:
    "/data/countries/tunisia/geojson/municipalities.geojson",

  featureProperty: "municipality_id",
  promoteId: "municipality_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 75,
    labelsPerZoom: 50,
  },

  initialView: TUNISIA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "municipality",
  },
});
