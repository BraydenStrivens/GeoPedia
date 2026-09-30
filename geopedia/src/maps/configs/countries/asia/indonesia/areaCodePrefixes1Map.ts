/**
 * Map configuration for Indonesia's 1-digit landline area-code prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaAreaCodePrefixes1Map = createMapConfig({
  id: "indonesia-area-code-prefixes-1",
  geojsonUrl:
    "/data/countries/indonesia/geojson/area-code-prefixes-1.geojson",

  featureProperty: "prefix_1",
  promoteId: "prefix_1",

  initialView: INDONESIA_INITIAL_VIEW,

  hover: {
    labelProperty: "display",
  },
});
