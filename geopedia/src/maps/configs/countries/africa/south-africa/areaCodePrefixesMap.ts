/**
 * Map configuration for South Africa's one-digit geographic telephone
 * area-code prefixes.
 *
 * Prefixes represent the first meaningful digit after South Africa's national
 * trunk prefix 0. The five map regions therefore correspond to prefixes
 * 1- through 5-.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaAreaCodePrefixesMap = createMapConfig({
  id: "south-africa-area-code-prefixes",
  geojsonUrl:
    "/data/countries/south-africa/geojson/area-code-prefixes.geojson",
  featureProperty: "prefix_1",
  promoteId: "prefix_id",
  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  hover: {
    labelProperty: "prefix_1",
  },
});
