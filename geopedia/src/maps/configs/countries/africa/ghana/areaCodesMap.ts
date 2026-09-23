/**
 * Map configuration for Ghana's geographic fixed-line area codes.
 *
 * Ghana's 16 current administrative regions are represented by 10 geographic
 * fixed-line numbering areas. Several current regions share an area code
 * because they were created by subdividing older administrative regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { GHANA_INITIAL_VIEW } from "./constants";

export const ghanaAreaCodesMap = createMapConfig({
  id: "ghana-area-codes",

  geojsonUrl: "/data/countries/ghana/geojson/area-codes.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  initialView: GHANA_INITIAL_VIEW,

  hover: {
    labelProperty: "regions",
  },
});
