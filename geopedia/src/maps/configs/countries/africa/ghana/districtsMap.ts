/**
 * Map configuration for Ghana's second-level administrative districts.
 *
 * Answer-label density is limited at lower zoom levels because Ghana contains
 * 260 districts, many of which are geographically small.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { GHANA_INITIAL_VIEW } from "./constants";

export const ghanaDistrictsMap = createMapConfig({
  id: "ghana-districts",

  geojsonUrl: "/data/countries/ghana/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: GHANA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "district",
  },
});
