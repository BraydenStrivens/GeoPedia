/**
 * Map configuration for South Africa's districts.
 *
 * Features use the canonical district_id property for map identity and
 * answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaDistrictsMap = createMapConfig({
  id: "south-africa-districts",
  geojsonUrl:
    "/data/countries/south-africa/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
