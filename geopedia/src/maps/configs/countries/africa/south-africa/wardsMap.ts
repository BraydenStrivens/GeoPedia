/**
 * Map configuration for South Africa's wards.
 *
 * Features use the canonical ward_id property for map identity and answers.
 * Answer labels are heavily throttled because the map contains more than
 * 4,000 wards.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaWardsMap = createMapConfig({
  id: "south-africa-wards",
  geojsonUrl: "/data/countries/south-africa/geojson/wards.geojson",

  featureProperty: "ward_id",
  promoteId: "ward_id",

  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 150,
    initialMaxLabels: 75,
    labelsPerZoom: 125,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "ward",
  },
});
