import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Mexico's 2,478 municipalities.
 *
 * Uses the five-digit INEGI municipality ID as the stable feature identifier
 * and municipality name for map interaction and hover labels.
 */
export const mexicoMunicipalitiesMap = createMapConfig({
  id: "mexico-municipalities",
  geojsonUrl: "/data/countries/mexico/geojson/municipalities.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "municipality_id",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: {
    center: [-102, 23.5],
    zoom: 3.6,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
