/**
 * Map configuration for Chile's first-digit postal-code prefix regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CHILE_INITIAL_VIEW } from "./constants";

export const chilePostalPrefixesMap = createMapConfig({
  id: "chile-postal-prefixes",

  geojsonUrl: "/data/countries/chile/geojson/postal-prefixes.geojson",

  featureProperty: "postal_prefix_id",
  promoteId: "postal_prefix_id",

  initialView: CHILE_INITIAL_VIEW,

  hover: {
    labelProperty: "postal_prefix",
  },
});
