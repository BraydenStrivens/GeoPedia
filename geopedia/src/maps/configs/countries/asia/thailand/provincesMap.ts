/**
 * Map configuration for Thailand's 77 province-level divisions,
 * including the Bangkok special administrative area.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { THAILAND_INITIAL_VIEW } from "./constants";

export const thailandProvincesMap = createMapConfig({
  id: "thailand-provinces",
  geojsonUrl: "/data/countries/thailand/geojson/provinces.geojson",

  featureProperty: "province",
  promoteId: "province_id",

  initialView: THAILAND_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "province",
  },
});
