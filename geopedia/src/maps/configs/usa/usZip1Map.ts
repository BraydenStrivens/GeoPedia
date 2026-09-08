/**
 * Defines the map configuration for the US 1-digit ZIP-code prefix quiz.
 *
 * Each feature represents a large geographic region containing all ZCTAs
 * that share the same first ZIP-code digit.
 */

import { createMapConfig } from "../createMapConfig";

export const usZip1Map = createMapConfig({
  id: "us-zip-1",
  geojsonUrl: "/data/countries/usa/geojson/zip-1.geojson",

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
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "zip",
  },
});
