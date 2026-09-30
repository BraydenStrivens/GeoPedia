/**
 * Map configuration for Malaysia's 2-digit telephone area-code prefixes.
 *
 * Feature identity is separate from the quiz answer because the same area code
 * can occur in more than one geographic feature.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MALAYSIA_INITIAL_VIEW } from "./constants";

export const malaysiaAreaCodePrefixes2Map = createMapConfig({
  id: "malaysia-area-code-prefixes-2",
  geojsonUrl:
    "/data/countries/malaysia/geojson/area-code-prefixes-2.geojson",

  featureProperty: "area_code_id",
  promoteId: "area_code_id",

  initialView: MALAYSIA_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code",
  },
});
