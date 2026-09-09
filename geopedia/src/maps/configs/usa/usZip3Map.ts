/**
 * Defines the map configuration for the US 3-digit ZIP-code prefix quiz.
 *
 * Each feature represents all ZCTAs sharing the same first three ZIP-code
 * digits.
 */

import { createMapConfig } from "../createMapConfig";

export const usZip3Map = createMapConfig({
  id: "us-zip-3",
  geojsonUrl: "/data/countries/usa/geojson/zip-3.geojson",

  featureProperty: "zip",

  style: {
    type: "maptiler",
  },

  promoteId: "id",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: {
    center: [-98.5, 39.8],
    zoom: 3.5,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "zip",
  },
});
