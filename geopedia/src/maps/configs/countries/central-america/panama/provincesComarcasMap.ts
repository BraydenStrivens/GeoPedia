import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Panama's 10 provinces and four province-level
 * comarcas.
 */
export const panamaProvincesComarcasMap = createMapConfig({
  id: "panama-provinces-comarcas",

  geojsonUrl:
    "/data/countries/panama/geojson/provinces-comarcas.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-80.5, 8.5],
    zoom: 5.7,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
