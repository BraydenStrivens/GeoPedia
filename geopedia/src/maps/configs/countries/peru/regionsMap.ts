import { createMapConfig } from "@/maps/configs/createMapConfig";

export const peruRegionsMap = createMapConfig({
  id: "peru-regions",
  geojsonUrl: "/data/countries/peru/geojson/regions.geojson",

  featureProperty: "region",
  promoteId: "region_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-75.2, -9.3],
    zoom: 4.8,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "region",
  },
});
