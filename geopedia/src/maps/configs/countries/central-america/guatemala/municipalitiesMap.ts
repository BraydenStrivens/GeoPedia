import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Guatemala's 342 municipalities.
 *
 * Uses the four-digit municipality p-code, normalized from the HDX source,
 * as the stable feature identifier and municipality name for map interaction
 * and hover labels.
 */
export const guatemalaMunicipalitiesMap = createMapConfig({
  id: "guatemala-municipalities",
  geojsonUrl:
    "/data/countries/guatemala/geojson/municipalities.geojson",
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
    center: [-90.25, 15.7],
    zoom: 5.5,
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
