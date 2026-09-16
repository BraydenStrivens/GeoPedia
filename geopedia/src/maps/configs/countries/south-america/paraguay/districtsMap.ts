/**
 * Map configuration for Paraguay's second-level administrative districts.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PARAGUAY_INITIAL_VIEW } from "./constants";

export const paraguayDistrictsMap = createMapConfig({
  id: "paraguay-districts",

  geojsonUrl: "/data/countries/paraguay/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: PARAGUAY_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
