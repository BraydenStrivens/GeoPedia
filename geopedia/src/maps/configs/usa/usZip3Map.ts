/**
 * Defines the map configuration for the US 3-digit ZIP-code prefix quiz.
 *
 * Each feature represents all ZCTAs sharing the same first three ZIP-code
 * digits.
 */

import type { MapConfig } from "../../types";

export const usZip3Map: MapConfig = {
  id: "us-zip-3",
  geojsonUrl: "/data/us-zip-3.geojson",

  featureProperty: "zip",

  style: {
    type: "maptiler",
  },

  promoteId: "id",

  initialView: {
    center: [-98.5, 39.8],
    zoom: 3.5,
  },

  layers: {
    fill: {
      color: "#969696",
      opacity: 0.35,
    },

    borders: {
      color: "#000000",
      width: 1,
    },
  },

  hover: {
    enabled: true,
    color: "#4e4e4e",
    labelProperty: "zip",
  },
};
