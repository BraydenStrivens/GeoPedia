/**
 * Map configuration for Peru's first-digit geographic telephone area-code
 * regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PERU_INITIAL_VIEW } from "./constants";

export const peruAreaCodes1DigitPrefixMap = createMapConfig({
  id: "peru-area-code-prefixes",
  geojsonUrl:
    "/data/countries/peru/geojson/area-code-prefixes.geojson",

  featureProperty: "area_code_prefix",
  promoteId: "area_code_prefix",

  initialView: PERU_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "area_code_prefix",
  },
});
