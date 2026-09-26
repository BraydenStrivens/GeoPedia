/**
 * Map configuration for South Korea's municipalities.
 *
 * Features use municipality_id as their stable map identity. Answer labels
 * are throttled because the map contains 250 municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_KOREA_INITIAL_VIEW } from "./constants";

export const southKoreaMunicipalitiesMap = createMapConfig({
  id: "south-korea-municipalities",
  geojsonUrl:
    "/data/countries/south-korea/geojson/municipalities.geojson",

  featureProperty: "municipality",
  promoteId: "municipality_id",

  initialView: SOUTH_KOREA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "municipality",
  },
});
