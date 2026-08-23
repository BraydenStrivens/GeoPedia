/**
 * Defines the map configuration for the US 1-digit ZIP-code prefix quiz.
 *
 * Each feature represents a large geographic region containing all ZCTAs
 * that share the same first ZIP-code digit.
 */

import type { MapConfig } from "../../types";

export const usZip1Map: MapConfig = {
  id: "us-zip-1",
  geojsonUrl: "/data/us-zip-1.geojson",

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
      width: 1.5,
    },
  },

  hover: {
    enabled: true,
    color: "#4e4e4e",
    labelProperty: "zip",
  },
};
