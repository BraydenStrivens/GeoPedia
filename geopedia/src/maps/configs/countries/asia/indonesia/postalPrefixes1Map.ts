/**
 * Map configuration for Indonesia's 1-digit postal-code prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaPostalPrefixes1Map = createMapConfig({
  id: "indonesia-postal-prefixes-1",

  geojsonUrl:
    "/data/countries/indonesia/geojson/postal-prefixes-1.geojson",

  featureProperty: "prefix_1",
  promoteId: "prefix_1",

  initialView: INDONESIA_INITIAL_VIEW,

  hover: {
    labelProperty: "prefix_1",
  },
});
