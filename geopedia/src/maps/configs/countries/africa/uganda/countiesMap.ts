/**
 * Map configuration for Uganda's counties.
 *
 * Features use the canonical county_id property for map identity and answers.
 * Answer labels are throttled because the map contains more than 200
 * subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { UGANDA_INITIAL_VIEW } from "./constants";

export const ugandaCountiesMap = createMapConfig({
  id: "uganda-counties",
  geojsonUrl: "/data/countries/uganda/geojson/counties.geojson",

  featureProperty: "county_id",
  promoteId: "county_id",

  initialView: UGANDA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 75,
    labelsPerZoom: 125,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "county",
  },
});
