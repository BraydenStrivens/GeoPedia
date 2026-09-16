import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Brazil's five geographic regions.
 */
export const brazilRegionsMap = createMapConfig({
  id: "brazil-regions",

  geojsonUrl: "/data/countries/brazil/geojson/regions.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-52.5, -14.5],
    zoom: 3.2,
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
