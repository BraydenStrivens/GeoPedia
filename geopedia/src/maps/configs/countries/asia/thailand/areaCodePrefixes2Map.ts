/**
 * Map configuration for Thailand's 21 geographic landline
 * area-code regions, grouped by their first significant digit.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { THAILAND_INITIAL_VIEW } from "./constants";

export const thailandAreaCodePrefixes2Map = createMapConfig({
  id: "thailand-area-code-prefixes-2",
  geojsonUrl:
    "/data/countries/thailand/geojson/area-code-prefixes-2.geojson",
  featureProperty: "area_code_prefix",
  promoteId: "area_code_prefix",

  initialView: THAILAND_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code_prefix",
  },
});
