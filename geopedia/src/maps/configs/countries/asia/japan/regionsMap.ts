/**
 * Map configuration for Japan's regions.
 *
 * Features use region_id as their stable map identity. Region names remain
 * available separately for hover labels and other player-facing UI.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { JAPAN_INITIAL_VIEW } from "./constants";

export const japanRegionsMap = createMapConfig({
  id: "japan-regions",
  geojsonUrl: "/data/countries/japan/geojson/regions.geojson",

  featureProperty: "region",
  promoteId: "region_id",

  initialView: JAPAN_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.25,
    },
  },

  hover: {
    labelProperty: "region",
  },
});
