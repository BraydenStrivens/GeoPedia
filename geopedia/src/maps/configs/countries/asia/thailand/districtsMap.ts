/**
 * Map configuration for Thailand's 928 district-level divisions,
 * including Bangkok's khet.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { THAILAND_INITIAL_VIEW } from "./constants";

export const thailandDistrictsMap = createMapConfig({
  id: "thailand-districts",
  geojsonUrl: "/data/countries/thailand/geojson/districts.geojson",

  featureProperty: "district",
  promoteId: "district_id",

  initialView: THAILAND_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "district",
  },
});
