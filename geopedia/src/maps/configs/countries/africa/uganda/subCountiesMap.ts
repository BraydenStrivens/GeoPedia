/**
 * Map configuration for Uganda's sub-counties.
 *
 * Features use the canonical sub_county_id property for map identity and
 * answers. Answer labels are throttled because the map contains more than
 * 1,500 subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { UGANDA_INITIAL_VIEW } from "./constants";

export const ugandaSubCountiesMap = createMapConfig({
  id: "uganda-sub-counties",
  geojsonUrl: "/data/countries/uganda/geojson/sub-counties.geojson",

  featureProperty: "sub_county_id",
  promoteId: "sub_county_id",

  initialView: UGANDA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 75,
    labelsPerZoom: 125,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "sub_county",
  },
});
