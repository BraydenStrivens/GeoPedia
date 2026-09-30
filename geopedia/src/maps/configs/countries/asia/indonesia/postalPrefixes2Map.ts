/**
 * Map configuration for Indonesia's 2-digit postal-code prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaPostalPrefixes2Map = createMapConfig({
  id: "indonesia-postal-prefixes-2",

  geojsonUrl:
    "/data/countries/indonesia/geojson/postal-prefixes-2.geojson",

  featureProperty: "prefix_2",
  promoteId: "prefix_2",

  initialView: INDONESIA_INITIAL_VIEW,

  hover: {
    labelProperty: "prefix_2",
  },
});
