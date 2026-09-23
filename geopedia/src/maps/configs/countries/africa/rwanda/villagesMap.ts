/**
 * Map configuration for Rwanda's imidugudu (villages).
 *
 * Features use the canonical village_id property for map identity and answers.
 * Answer labels are heavily throttled because the map contains nearly 15,000
 * subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { RWANDA_INITIAL_VIEW } from "./constants";

export const rwandaVillagesMap = createMapConfig({
  id: "rwanda-villages",
  geojsonUrl: "/data/countries/rwanda/geojson/villages.geojson",

  featureProperty: "village_id",
  promoteId: "village_id",

  initialView: RWANDA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 75,
    labelsPerZoom: 125,
  },

  layers: {
    borders: {
      width: 0.25,
    },
  },

  hover: {
    labelProperty: "village",
  },
});
