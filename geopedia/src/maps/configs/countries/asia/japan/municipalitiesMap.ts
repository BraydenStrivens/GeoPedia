/**
 * Map configuration for Japan's municipalities.
 *
 * Features use municipality_id as their stable map identity. Answer labels
 * are throttled because the map contains 1,892 municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { JAPAN_INITIAL_VIEW } from "./constants";

export const japanMunicipalitiesMap = createMapConfig({
  id: "japan-municipalities",
  geojsonUrl: "/data/countries/japan/geojson/municipalities.geojson",

  featureProperty: "municipality",
  promoteId: "municipality_id",

  initialView: JAPAN_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "municipality",
  },
});
