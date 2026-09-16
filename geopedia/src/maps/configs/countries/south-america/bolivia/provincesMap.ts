import { createMapConfig } from "@/maps/configs/createMapConfig";

export const boliviaProvincesMap = createMapConfig({
  id: "bolivia-provinces",

  geojsonUrl: "/data/countries/bolivia/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-64.7, -16.7],
    zoom: 4.6,
  },

  hover: {
    labelProperty: "province",
  },
});
