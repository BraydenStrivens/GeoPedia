/**
 * Map configuration for Japan's broad telephone area-code prefixes.
 *
 * The 9 regions are derived by dissolving Japan's 59 area-code regions
 * according to their first significant digit. Features use prefix_id as
 * their stable map identity and labels use the 0X- display format.
 */
import { createMapConfig } from "@/maps/configs/createMapConfig";

import { JAPAN_INITIAL_VIEW } from "./constants";

export const japanAreaCodePrefixesMap = createMapConfig({
  id: "japan-area-code-prefixes",
  geojsonUrl:
    "/data/countries/japan/geojson/area-code-prefixes.geojson",

  featureProperty: "prefix",
  promoteId: "prefix_id",

  initialView: JAPAN_INITIAL_VIEW,

  hover: {
    labelProperty: "prefix",
  },
});
