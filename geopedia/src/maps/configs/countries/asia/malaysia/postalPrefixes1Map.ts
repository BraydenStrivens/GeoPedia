/**
 * Map configuration for Malaysia's 1-digit postal-code prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MALAYSIA_INITIAL_VIEW } from "./constants";

export const malaysiaPostalPrefixes1Map = createMapConfig({
  id: "malaysia-postal-prefixes-1",
  geojsonUrl:
    "/data/countries/malaysia/geojson/postal-prefixes-1.geojson",

  featureProperty: "post_code",
  promoteId: "post_code",

  initialView: MALAYSIA_INITIAL_VIEW,

  hover: {
    labelProperty: "post_code",
  },
});
