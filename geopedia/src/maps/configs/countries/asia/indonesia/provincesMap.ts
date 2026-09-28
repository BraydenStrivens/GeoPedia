/**
 * Map configuration for Indonesia's first-level administrative provinces.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaProvincesMap = createMapConfig({
  id: "indonesia-provinces",

  geojsonUrl: "/data/countries/indonesia/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: INDONESIA_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
