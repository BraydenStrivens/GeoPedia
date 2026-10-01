/**
 * Map configuration for Vietnam's pre-reform first-level administrative
 * provinces and centrally governed municipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { VIETNAM_INITIAL_VIEW } from "./constants";

export const vietnamPreReformProvincesMap = createMapConfig({
  id: "vietnam-pre-reform-provinces",
  geojsonUrl:
    "/data/countries/vietnam/geojson/pre-reform-provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: VIETNAM_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
