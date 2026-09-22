/**
 * Map configuration for Senegal's first-level administrative regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SENEGAL_INITIAL_VIEW } from "./constants";

export const senegalRegionsMap = createMapConfig({
  id: "senegal-regions",

  geojsonUrl: "/data/countries/senegal/geojson/regions.geojson",

  featureProperty: "region_id",
  promoteId: "region_id",

  initialView: SENEGAL_INITIAL_VIEW,

  hover: {
    labelProperty: "region",
  },
});
