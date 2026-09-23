/**
 * Map configuration for Uganda's districts.
 *
 * Features use the canonical district_id property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { UGANDA_INITIAL_VIEW } from "./constants";

export const ugandaDistrictsMap = createMapConfig({
  id: "uganda-districts",
  geojsonUrl: "/data/countries/uganda/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  initialView: UGANDA_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
