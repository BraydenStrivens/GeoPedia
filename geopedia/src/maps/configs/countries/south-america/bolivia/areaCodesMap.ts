import { createMapConfig } from "@/maps/configs/createMapConfig";

export const boliviaAreaCodesMap = createMapConfig({
  id: "bolivia-area-codes",

  geojsonUrl: "/data/countries/bolivia/geojson/area-codes.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-64.7, -16.7],
    zoom: 4.6,
  },

  hover: {
    labelProperty: "area_code",
  },
});
