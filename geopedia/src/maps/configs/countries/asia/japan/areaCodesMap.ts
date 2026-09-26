/**
 * Map configuration for Japan's telephone area-code regions.
 *
 * The map contains 59 normalized area-code regions. Features use
 * area_code_id as their stable map identity while area_code provides
 * the player-facing label.
 */
import { createMapConfig } from "@/maps/configs/createMapConfig";

import { JAPAN_INITIAL_VIEW } from "./constants";

export const japanAreaCodesMap = createMapConfig({
  id: "japan-area-codes",
  geojsonUrl: "/data/countries/japan/geojson/area-codes.geojson",

  featureProperty: "area_code",
  promoteId: "area_code_id",

  initialView: JAPAN_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code",
  },
});
