/**
 * Defines the map configuration for the United States counties quiz.
 *
 * Each feature represents one Census county or county-equivalent and uses
 * its GEOID as a stable unique identifier.
 */

import type { MapConfig } from "../../types";

export const usCountiesMap: MapConfig = {
  id: "us-counties",
  geojsonUrl: "/data/us-counties.geojson",

  featureProperty: "geoid",

  style: {
    type: "maptiler",
  },

  promoteId: "geoid",
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
    fill: {
      color: "#969696",
      opacity: 0.35,
    },

    borders: {
      color: "#000000",
      width: 0.8,
    },
  },

  hover: {
    enabled: true,
    color: "#4e4e4e",
    labelProperty: "fullName",
  },
};
