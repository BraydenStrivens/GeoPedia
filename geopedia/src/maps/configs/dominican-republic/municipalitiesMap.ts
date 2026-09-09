import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for the Dominican Republic's 155 municipalities.
 */
export const dominicanRepublicMunicipalitiesMap = createMapConfig({
  id: "dominican-republic-municipalities",
  geojsonUrl:
    "/data/countries/dominican-republic/geojson/municipalities.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "municipality_id",

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  initialView: {
    center: [-70.4, 18.8],
    zoom: 6,
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
