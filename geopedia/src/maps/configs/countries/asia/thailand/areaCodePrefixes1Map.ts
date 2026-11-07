/**
 * Map configuration for Thailand's five geographic landline
 * area-code prefix regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { THAILAND_INITIAL_VIEW } from "./constants";

export const thailandAreaCodePrefixes1Map = createMapConfig({
  id: "thailand-area-code-prefixes-1",
  geojsonUrl:
    "/data/countries/thailand/geojson/area-code-prefixes-1.geojson",
  featureProperty: "area_code_prefix",
  promoteId: "area_code_prefix",

  initialView: THAILAND_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code_prefix",
  },
});
