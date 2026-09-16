import { createMapConfig } from "@/maps/configs/createMapConfig";

export const ecuadorAreaCodesMap = createMapConfig({
  id: "ecuador-area-codes",
  geojsonUrl: "/data/countries/ecuador/geojson/area-codes.geojson",

  featureProperty: "area_code",
  promoteId: "area_code_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-83.5, -1.4],
    zoom: 3.8,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
