/**
 * Map configuration for the Dominican Republic's municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { DOMINICAN_REPUBLIC_INITIAL_VIEW } from "./constants";

export const dominicanRepublicMunicipalitiesMap = createMapConfig({
  id: "dominican-republic-municipalities",
  geojsonUrl:
    "/data/countries/dominican-republic/geojson/municipalities.geojson",
  featureProperty: "name",

  promoteId: "municipality_id",

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  initialView: DOMINICAN_REPUBLIC_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
