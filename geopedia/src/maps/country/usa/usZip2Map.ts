/**
 * Defines the map configuration for the US 2-digit ZIP-code prefix quiz.
 *
 * Each feature represents all ZCTAs sharing the same first two ZIP-code
 * digits.
 */

import type { MapConfig } from "../../types";

export const usZip2Map: MapConfig = {
  id: "us-zip-2",
  geojsonUrl: "/data/us-zip-2.geojson",

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
      width: 1.25,
    },
  },

  hover: {
    enabled: true,
    color: "#4e4e4e",
    labelProperty: "zip",
  },
};
