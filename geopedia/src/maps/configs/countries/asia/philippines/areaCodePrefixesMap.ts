/**
 * Map configuration for the Philippines' one-digit telephone area-code
 * prefixes.
 *
 * Features use the domestic prefix_1 property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PHILIPPINES_INITIAL_VIEW } from "./constants";

export const philippinesAreaCodePrefixesMap = createMapConfig({
  id: "philippines-area-code-prefixes",
  geojsonUrl:
    "/data/countries/philippines/geojson/area-code-prefixes.geojson",

  featureProperty: "prefix_1",
  promoteId: "prefix_1",

  initialView: PHILIPPINES_INITIAL_VIEW,

  hover: {
    labelProperty: "prefix_1",
  },
});
