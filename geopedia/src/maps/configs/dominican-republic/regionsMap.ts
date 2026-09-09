import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for the Dominican Republic's 10 administrative regions.
 */
export const dominicanRepublicRegionsMap = createMapConfig({
  id: "dominican-republic-regions",
  geojsonUrl:
    "/data/countries/dominican-republic/geojson/regions.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "region_id",

  initialView: {
    center: [-70.4, 18.8],
    zoom: 6,
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
