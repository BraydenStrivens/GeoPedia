/**
 * Map configuration for Lesotho's districts.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { LESOTHO_INITIAL_VIEW } from "./constants";

export const lesothoDistrictsMap = createMapConfig({
  id: "lesotho-districts",
  geojsonUrl: "/data/countries/lesotho/geojson/districts.geojson",

  featureProperty: "district",
  promoteId: "district_id",

  initialView: LESOTHO_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
