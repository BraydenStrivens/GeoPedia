/**
 * Map configuration for Mexico's municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MEXICO_INITIAL_VIEW } from "./constants";

export const mexicoMunicipalitiesMap = createMapConfig({
  id: "mexico-municipalities",
  geojsonUrl: "/data/countries/mexico/geojson/municipalities.geojson",
  featureProperty: "name",

  promoteId: "municipality_id",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: MEXICO_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
