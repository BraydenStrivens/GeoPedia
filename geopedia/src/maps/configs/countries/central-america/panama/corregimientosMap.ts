/**
 * Map configuration for Panama's corregimientos.
 *
 * The processed GeoJSON contains 698 unique administrative features. Repeated
 * geographic names remain separate because each corregimiento has its own
 * stable six-digit ID.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PANAMA_INITIAL_VIEW } from "./constants";

export const panamaCorregimientosMap = createMapConfig({
  id: "panama-corregimientos",

  geojsonUrl: "/data/countries/panama/geojson/corregimientos.geojson",

  featureProperty: "name",
  promoteId: "id",

  answerLabels: {
    densityThreshold: 250,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: PANAMA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
