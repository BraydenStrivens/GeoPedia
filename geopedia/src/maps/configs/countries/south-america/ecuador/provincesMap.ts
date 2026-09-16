import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Ecuador's 24 provinces.
 *
 * Each feature uses the official ADM1 PCODE as its stable feature ID and
 * stores the province name in the `province` property.
 */
export const ecuadorProvincesMap = createMapConfig({
  id: "ecuador-provinces",

  geojsonUrl: "/data/countries/ecuador/geojson/provinces.geojson",

  featureProperty: "province",
  promoteId: "province_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-83.5, -1.4],
    zoom: 5,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "province",
  },
});
