import { createMapConfig } from "@/maps/configs/createMapConfig";

export const paraguayDistrictsMap = createMapConfig({
  id: "paraguay-districts",

  geojsonUrl: "/data/countries/paraguay/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  style: {
    type: "maptiler",
  },

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: {
    center: [-58.3, -23.4],
    zoom: 4.9,
  },

  hover: {
    labelProperty: "district",
  },
});
