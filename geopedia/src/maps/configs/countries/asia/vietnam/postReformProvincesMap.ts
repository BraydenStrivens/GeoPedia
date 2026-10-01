/**
 * Map configuration for Vietnam's post-reform first-level administrative
 * provinces and centrally governed cities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { VIETNAM_INITIAL_VIEW } from "./constants";

export const vietnamPostReformProvincesMap = createMapConfig({
  id: "vietnam-post-reform-provinces",
  geojsonUrl:
    "/data/countries/vietnam/geojson/post-reform-provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: VIETNAM_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
