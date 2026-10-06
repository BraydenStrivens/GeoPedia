/**
 * Map configuration for Cambodia's merged one-digit geographic
 * landline area-code prefix regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CAMBODIA_INITIAL_VIEW } from "./constants";

export const cambodiaAreaCodePrefixesMap = createMapConfig({
  id: "cambodia-area-code-prefixes",
  geojsonUrl:
    "/data/countries/cambodia/geojson/area-code-prefixes.geojson",

  featureProperty: "area_code_prefix",
  promoteId: "area_code_prefix",

  initialView: CAMBODIA_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code_prefix",
  },
});
