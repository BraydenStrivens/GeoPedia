/**
 * Map configuration for Malaysia's second-level administrative districts.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MALAYSIA_INITIAL_VIEW } from "./constants";

export const malaysiaDistrictsMap = createMapConfig({
  id: "malaysia-districts",
  geojsonUrl: "/data/countries/malaysia/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  initialView: MALAYSIA_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
