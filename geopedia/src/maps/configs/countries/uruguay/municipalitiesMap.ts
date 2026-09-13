import { createMapConfig } from "@/maps/configs/createMapConfig";

export const uruguayMunicipalitiesMap = createMapConfig({
  id: "uruguay-municipalities",

  geojsonUrl:
    "/data/countries/uruguay/geojson/municipalities.geojson",

  featureProperty: "municipality_id",
  promoteId: "municipality_id",

  initialView: {
    center: [-56.0, -32.8],
    zoom: 5.5,
  },

  hover: {
    labelProperty: "municipality",
  },

  style: {
    type: "maptiler",
  },
});
