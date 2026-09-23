/**
 * Map configuration for Ghana's first-level administrative regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { GHANA_INITIAL_VIEW } from "./constants";

export const ghanaRegionsMap = createMapConfig({
  id: "ghana-regions",

  geojsonUrl: "/data/countries/ghana/geojson/regions.geojson",

  featureProperty: "region_id",
  promoteId: "region_id",

  initialView: GHANA_INITIAL_VIEW,

  hover: {
    labelProperty: "region",
  },
});
