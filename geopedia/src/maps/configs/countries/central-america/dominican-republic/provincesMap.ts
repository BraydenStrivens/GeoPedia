/**
 * Map configuration for the Dominican Republic's provinces and
 * province-equivalent divisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { DOMINICAN_REPUBLIC_INITIAL_VIEW } from "./constants";

export const dominicanRepublicProvincesMap = createMapConfig({
  id: "dominican-republic-provinces",
  geojsonUrl:
    "/data/countries/dominican-republic/geojson/provinces.geojson",
  featureProperty: "name",

  promoteId: "province_id",

  initialView: DOMINICAN_REPUBLIC_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
