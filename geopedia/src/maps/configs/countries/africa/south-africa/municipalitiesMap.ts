/**
 * Map configuration for South Africa's municipalities.
 *
 * Features use the canonical municipality_id property for map identity and
 * answers. Answer labels are throttled because this map contains more than
 * 200 municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaMunicipalitiesMap = createMapConfig({
  id: "south-africa-municipalities",
  geojsonUrl:
    "/data/countries/south-africa/geojson/municipalities.geojson",

  featureProperty: "municipality_id",
  promoteId: "municipality_id",

  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 150,
    initialMaxLabels: 75,
    labelsPerZoom: 125,
  },

  hover: {
    labelProperty: "municipality",
  },
});
