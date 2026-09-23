/**
 * Map configuration for Kenya's sub-counties.
 *
 * Features use the canonical sub_county_id property for map identity and
 * answers. Answer labels are throttled because the map contains 290
 * subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { KENYA_INITIAL_VIEW } from "./constants";

export const kenyaSubCountiesMap = createMapConfig({
  id: "kenya-sub-counties",
  geojsonUrl: "/data/countries/kenya/geojson/sub-counties.geojson",

  featureProperty: "sub_county_id",
  promoteId: "sub_county_id",

  initialView: KENYA_INITIAL_VIEW,

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
    labelProperty: "sub_county",
  },
});
