import { createMapConfig } from "@/maps/configs/createMapConfig";

export const argentinaProvincesMap = createMapConfig({
  id: "argentina-provinces",

  geojsonUrl: "/data/countries/argentina/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-64.5, -38.5],
    zoom: 3.4,
  },

  hover: {
    labelProperty: "province",
  },
});
