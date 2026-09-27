/**
 * Map configuration for Taiwan's township-level divisions.
 *
 * The map contains 368 townships, districts, and county-administered
 * cities. Features use township_id as their stable map identity while
 * township provides the player-facing label.
 *
 * Answer labels are throttled because of the map's high feature count.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TAIWAN_INITIAL_VIEW } from "./constants";

export const taiwanTownshipsMap = createMapConfig({
  id: "taiwan-townships",
  geojsonUrl: "/data/countries/taiwan/geojson/townships.geojson",

  featureProperty: "township",
  promoteId: "township_id",

  initialView: TAIWAN_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "township",
  },
});
