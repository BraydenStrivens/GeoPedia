/**
 * Map configuration for Malaysia's 1-digit telephone area-code prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MALAYSIA_INITIAL_VIEW } from "./constants";

export const malaysiaAreaCodePrefixes1Map = createMapConfig({
  id: "malaysia-area-code-prefixes-1",
  geojsonUrl:
    "/data/countries/malaysia/geojson/area-code-prefixes-1.geojson",

  featureProperty: "area_code_id",
  promoteId: "area_code_id",

  initialView: MALAYSIA_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code",
  },
});
