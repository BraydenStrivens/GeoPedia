/**
 * Map configuration for Japan's pole-meta regions.
 *
 * Features use region_id as their stable map identity. Region names remain
 * available separately for hover labels and other player-facing UI.
 *
 * The 10 regions group prefectures by shared utility-pole characteristics
 * used by the pole plate and pole top quizzes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { JAPAN_INITIAL_VIEW } from "./constants";

export const japanPoleMetaRegionsMap = createMapConfig({
  id: "japan-pole-meta-regions",
  geojsonUrl:
    "/data/countries/japan/geojson/pole-meta-regions.geojson",

  featureProperty: "pole_meta_region_id",
  promoteId: "pole_meta_region_id",

  initialView: JAPAN_INITIAL_VIEW,

  hover: {
    labelProperty: "pole_meta_region",
  },
});
