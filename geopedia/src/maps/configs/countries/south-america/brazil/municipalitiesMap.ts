/**
 * Map configuration for Brazil's municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BRAZIL_INITIAL_VIEW } from "./constants";

export const brazilMunicipalitiesMap = createMapConfig({
  id: "brazil-municipalities",

  geojsonUrl: "/data/countries/brazil/geojson/municipalities.geojson",

  featureProperty: "name",
  promoteId: "id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: BRAZIL_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
