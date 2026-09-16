import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Ecuador's 221 cantons.
 *
 * Each feature uses the official ADM2 PCODE as its stable feature ID.
 * Province information is retained on each feature for quiz grouping.
 */
export const ecuadorCantonsMap = createMapConfig({
  id: "ecuador-cantons",

  geojsonUrl: "/data/countries/ecuador/geojson/cantons.geojson",

  featureProperty: "canton",
  promoteId: "canton_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-83.5, -1.4],
    zoom: 5,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "canton",
  },
});
