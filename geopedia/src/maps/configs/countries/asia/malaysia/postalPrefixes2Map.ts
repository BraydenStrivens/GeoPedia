/**
 * Map configuration for Malaysia's 2-digit postal-code prefixes.
 *
 * The underlying geography also includes each prefix's first digit for
 * grouping the corresponding quiz into smaller practice sets.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MALAYSIA_INITIAL_VIEW } from "./constants";

export const malaysiaPostalPrefixes2Map = createMapConfig({
  id: "malaysia-postal-prefixes-2",
  geojsonUrl:
    "/data/countries/malaysia/geojson/postal-prefixes-2.geojson",

  featureProperty: "post_code",
  promoteId: "post_code",

  initialView: MALAYSIA_INITIAL_VIEW,

  hover: {
    labelProperty: "post_code",
  },
});
