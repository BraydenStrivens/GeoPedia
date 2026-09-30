/**
 * Map configuration for Indonesia's 2-digit landline area-code prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaAreaCodePrefixes2Map = createMapConfig({
  id: "indonesia-area-code-prefixes-2",
  geojsonUrl:
    "/data/countries/indonesia/geojson/area-code-prefixes-2.geojson",

  featureProperty: "prefix_2",
  promoteId: "prefix_2",

  initialView: INDONESIA_INITIAL_VIEW,

  hover: {
    labelProperty: "display",
  },
});
