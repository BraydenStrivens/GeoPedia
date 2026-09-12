import { createMapConfig } from "@/maps/configs/createMapConfig";

export const boliviaMunicipalitiesMap = createMapConfig({
  id: "bolivia-municipalities",

  geojsonUrl:
    "/data/countries/bolivia/geojson/municipalities.geojson",

  featureProperty: "municipality_id",
  promoteId: "municipality_id",

  style: {
    type: "maptiler",
  },

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: {
    center: [-64.7, -16.7],
    zoom: 4.6,
  },

  hover: {
    labelProperty: "municipality",
  },
});
