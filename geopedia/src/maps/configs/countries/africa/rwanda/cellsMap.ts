/**
 * Map configuration for Rwanda's utugali (cells).
 *
 * Features use the canonical cell_id property for map identity and answers.
 * Answer labels are throttled because the map contains more than 2,000
 * subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { RWANDA_INITIAL_VIEW } from "./constants";

export const rwandaCellsMap = createMapConfig({
  id: "rwanda-cells",
  geojsonUrl: "/data/countries/rwanda/geojson/cells.geojson",

  featureProperty: "cell_id",
  promoteId: "cell_id",

  initialView: RWANDA_INITIAL_VIEW,

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
    labelProperty: "cell",
  },
});
