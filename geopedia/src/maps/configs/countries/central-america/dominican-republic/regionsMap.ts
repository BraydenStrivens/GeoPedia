/**
 * Map configuration for the Dominican Republic's administrative regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { DOMINICAN_REPUBLIC_INITIAL_VIEW } from "./constants";

export const dominicanRepublicRegionsMap = createMapConfig({
  id: "dominican-republic-regions",
  geojsonUrl:
    "/data/countries/dominican-republic/geojson/regions.geojson",
  featureProperty: "name",

  promoteId: "region_id",

  initialView: DOMINICAN_REPUBLIC_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
