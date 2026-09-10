import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Panama's corregimientos.
 *
 * The processed GeoJSON contains 698 unique administrative features. Repeated
 * geographic names remain separate because each corregimiento has its own
 * stable six-digit ID.
 */
export const panamaCorregimientosMap = createMapConfig({
  id: "panama-corregimientos",

  geojsonUrl: "/data/countries/panama/geojson/corregimientos.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  answerLabels: {
    densityThreshold: 250,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: {
    center: [-80.5, 8.5],
    zoom: 5.7,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
