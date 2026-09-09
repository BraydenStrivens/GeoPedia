/**
 * Defines the map configuration for the United States counties quiz.
 *
 * Each feature represents one Census county or county-equivalent and uses
 * its GEOID as a stable unique identifier.
 */

import { createMapConfig } from "../createMapConfig";

export const usCountiesMap = createMapConfig({
  id: "us-counties",
  geojsonUrl: "/data/countries/usa/geojson/counties.geojson",

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
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "fullName",
  },
});
