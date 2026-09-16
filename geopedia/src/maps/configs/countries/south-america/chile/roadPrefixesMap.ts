/**
 * Map configuration for Chile's regional road-letter prefix areas.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CHILE_INITIAL_VIEW } from "./constants";

export const chileRoadPrefixesMap = createMapConfig({
  id: "chile-road-prefixes",

  geojsonUrl: "/data/countries/chile/geojson/road-prefixes.geojson",

  featureProperty: "road_prefix_id",
  promoteId: "road_prefix_id",

  initialView: CHILE_INITIAL_VIEW,

  hover: {
    labelProperty: "road_prefix",
  },
});
