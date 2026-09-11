/**
 * Defines the map configuration for the US 2-digit ZIP-code prefix quiz.
 *
 * Each feature represents all ZCTAs sharing the same first two ZIP-code
 * digits.
 */

import { createMapConfig } from "../../createMapConfig";

export const usZip2Map = createMapConfig({
  id: "us-zip-2",
  geojsonUrl: "/data/countries/usa/geojson/zip-2.geojson",

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
      width: 1.25,
    },
  },

  hover: {
    labelProperty: "zip",
  },
});
