import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Brazil's municipalities.
 */
export const brazilMunicipalitiesMap = createMapConfig({
  id: "brazil-municipalities",

  geojsonUrl: "/data/countries/brazil/geojson/municipalities.geojson",

  featureProperty: "name",
  promoteId: "id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-52.5, -14.5],
    zoom: 3.2,
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
