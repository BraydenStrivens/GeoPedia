import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Ecuador's 1,042 parishes.
 *
 * Each feature uses the official ADM3 PCODE as its stable feature ID.
 * Canton and province information are retained on each feature for quiz
 * grouping.
 */
export const ecuadorParishesMap = createMapConfig({
  id: "ecuador-parishes",

  geojsonUrl: "/data/countries/ecuador/geojson/parishes.geojson",

  featureProperty: "parish",
  promoteId: "parish_id",

  answerLabels: {
    densityThreshold: 250,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
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
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "parish",
  },
});
