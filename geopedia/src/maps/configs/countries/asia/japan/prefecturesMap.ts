/**
 * Map configuration for Japan's prefectures.
 *
 * Features use prefecture_id as their stable map identity. Prefecture names
 * remain available separately for hover labels and other player-facing UI.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { JAPAN_INITIAL_VIEW } from "./constants";

export const japanPrefecturesMap = createMapConfig({
  id: "japan-prefectures",
  geojsonUrl: "/data/countries/japan/geojson/prefectures.geojson",

  featureProperty: "prefecture",
  promoteId: "prefecture_id",

  initialView: JAPAN_INITIAL_VIEW,

  hover: {
    labelProperty: "prefecture",
  },
});
