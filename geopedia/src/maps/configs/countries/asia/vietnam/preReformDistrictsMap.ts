/**
 * Map configuration for Vietnam's pre-reform second-level districts.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { VIETNAM_INITIAL_VIEW } from "./constants";

export const vietnamPreReformDistrictsMap = createMapConfig({
  id: "vietnam-pre-reform-districts",
  geojsonUrl:
    "/data/countries/vietnam/geojson/pre-reform-districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  initialView: VIETNAM_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "district",
  },
});
