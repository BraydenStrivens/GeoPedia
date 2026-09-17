/**
 * Map configuration for Colombia's second-level administrative municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { COLOMBIA_INITIAL_VIEW } from "./constants";

export const colombiaMunicipalitiesMap = createMapConfig({
  id: "colombia-municipalities",

  geojsonUrl:
    "/data/countries/colombia/geojson/municipalities.geojson",

  featureProperty: "name",
  promoteId: "id",

  answerLabels: {
    densityThreshold: 200,
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
    labelProperty: "name",
  },
});
