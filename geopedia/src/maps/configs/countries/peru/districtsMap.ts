import { createMapConfig } from "@/maps/configs/createMapConfig";

export const peruDistrictsMap = createMapConfig({
  id: "peru-districts",
  geojsonUrl: "/data/countries/peru/geojson/districts.geojson",

  featureProperty: "district",
  promoteId: "district_id",

  answerLabels: {
    densityThreshold: 300,
    initialMaxLabels: 100,
    labelsPerZoom: 200,
  },

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-75.2, -9.3],
    zoom: 4.8,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "district",
  },
});
