/**
 * Map configuration for Guatemala's 342 municipalities.
 *
 * Uses the four-digit municipality p-code, normalized from the HDX source,
 * as the stable feature identifier and municipality name for map interaction
 * and hover labels.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { GUATEMALA_INITIAL_VIEW } from "./constants";

export const guatemalaMunicipalitiesMap = createMapConfig({
  id: "guatemala-municipalities",
  geojsonUrl:
    "/data/countries/guatemala/geojson/municipalities.geojson",
  featureProperty: "name",

  promoteId: "municipality_id",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: GUATEMALA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
