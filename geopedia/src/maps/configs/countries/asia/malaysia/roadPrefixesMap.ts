/**
 * Map configuration for Malaysia's state road-prefix regions.
 *
 * Federal territories without their own state road-prefix geography are
 * excluded or incorporated into the surrounding state as appropriate.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MALAYSIA_INITIAL_VIEW } from "./constants";

export const malaysiaRoadPrefixesMap = createMapConfig({
  id: "malaysia-road-prefixes",
  geojsonUrl:
    "/data/countries/malaysia/geojson/road-prefixes.geojson",

  featureProperty: "road_prefix_id",
  promoteId: "road_prefix_id",

  initialView: MALAYSIA_INITIAL_VIEW,

  hover: {
    labelProperty: "state",
  },
});
