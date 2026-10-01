/**
 * Map configuration for Vietnam's two-digit telephone area-code prefixes.
 *
 * Regions are derived by dissolving the province boundaries that share the
 * same first two area-code digits.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { VIETNAM_INITIAL_VIEW } from "./constants";

export const vietnamAreaCodePrefixes2Map = createMapConfig({
  id: "vietnam-area-code-prefixes-2",
  geojsonUrl:
    "/data/countries/vietnam/geojson/area-code-prefixes-2.geojson",

  featureProperty: "area_code_prefix",
  promoteId: "area_code_prefix",

  initialView: VIETNAM_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code_prefix",
  },
});
