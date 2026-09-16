/**
 * Map configuration for Bolivia's second-level administrative provinces.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BOLIVIA_INITIAL_VIEW } from "./constants";

export const boliviaProvincesMap = createMapConfig({
  id: "bolivia-provinces",

  geojsonUrl: "/data/countries/bolivia/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: BOLIVIA_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
