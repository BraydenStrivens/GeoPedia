import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Colombia's municipalities.
 */
export const colombiaMunicipalitiesMap = createMapConfig({
  id: "colombia-municipalities",

  geojsonUrl:
    "/data/countries/colombia/geojson/municipalities.geojson",

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
    center: [-74.3, 4.5],
    zoom: 4.6,
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
