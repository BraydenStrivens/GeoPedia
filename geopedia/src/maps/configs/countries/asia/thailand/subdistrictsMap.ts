/**
 * Map configuration for Thailand's 7,425 subdistrict-level divisions,
 * including Bangkok's khwaeng.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { THAILAND_INITIAL_VIEW } from "./constants";

export const thailandSubdistrictsMap = createMapConfig({
  id: "thailand-subdistricts",
  geojsonUrl: "/data/countries/thailand/geojson/subdistricts.geojson",

  featureProperty: "subdistrict",
  promoteId: "subdistrict_id",

  initialView: THAILAND_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "subdistrict",
  },
});
