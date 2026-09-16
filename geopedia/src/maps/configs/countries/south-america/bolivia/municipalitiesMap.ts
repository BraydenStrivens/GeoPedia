/**
 * Map configuration for Bolivia's third-level administrative municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BOLIVIA_INITIAL_VIEW } from "./constants";

export const boliviaMunicipalitiesMap = createMapConfig({
  id: "bolivia-municipalities",

  geojsonUrl:
    "/data/countries/bolivia/geojson/municipalities.geojson",

  featureProperty: "municipality_id",
  promoteId: "municipality_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: BOLIVIA_INITIAL_VIEW,

  hover: {
    labelProperty: "municipality",
  },
});
