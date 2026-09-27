/**
 * Map configuration for Taiwan's county-road prefix characters.
 *
 * The map contains 17 road-prefix regions derived from Taiwan's county-level
 * geometry. Sixteen features represent unique county or municipality prefix
 * characters, while Keelung City, Hsinchu City, and Chiayi City are combined
 * into a single MultiPolygon feature because all three use 市.
 *
 * Taipei City, Kinmen County, and Lienchiang County are excluded because they
 * do not have unique prefix characters on the reference map used for this
 * quiz.
 *
 * Features use road_prefix_id as their stable map identity while road_prefix
 * provides the player-facing character.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TAIWAN_INITIAL_VIEW } from "./constants";

export const taiwanRoadPrefixesMap = createMapConfig({
  id: "taiwan-road-prefixes",
  geojsonUrl: "/data/countries/taiwan/geojson/road-prefixes.geojson",

  featureProperty: "road_prefix",
  promoteId: "road_prefix_id",

  initialView: TAIWAN_INITIAL_VIEW,

  hover: {
    labelProperty: "road_prefix",
  },
});
