import { createMapConfig } from "@/maps/configs/createMapConfig";

export const peruProvincesMap = createMapConfig({
  id: "peru-provinces",
  geojsonUrl: "/data/countries/peru/geojson/provinces.geojson",

  featureProperty: "province",
  promoteId: "province_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
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
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "province",
  },
});
