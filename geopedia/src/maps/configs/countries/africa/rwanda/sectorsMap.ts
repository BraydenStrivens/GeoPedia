/**
 * Map configuration for Rwanda's imirenge (sectors).
 *
 * Features use the canonical sector_id property for map identity and answers.
 * Answer labels are throttled because the map contains hundreds of subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { RWANDA_INITIAL_VIEW } from "./constants";

export const rwandaSectorsMap = createMapConfig({
  id: "rwanda-sectors",
  geojsonUrl: "/data/countries/rwanda/geojson/sectors.geojson",

  featureProperty: "sector_id",
  promoteId: "sector_id",

  initialView: RWANDA_INITIAL_VIEW,

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
    labelProperty: "sector",
  },
});
