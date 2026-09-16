import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for the Dominican Republic's 32 province-level
 * administrative divisions.
 */
export const dominicanRepublicProvincesMap = createMapConfig({
  id: "dominican-republic-provinces",
  geojsonUrl:
    "/data/countries/dominican-republic/geojson/provinces.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "province_id",

  initialView: {
    center: [-70.4, 18.8],
    zoom: 6,
  },

  hover: {
    labelProperty: "name",
  },
});
