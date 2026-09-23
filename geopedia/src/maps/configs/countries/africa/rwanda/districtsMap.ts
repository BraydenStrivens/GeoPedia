/**
 * Map configuration for Rwanda's uturere (districts).
 *
 * Features use the canonical district_id property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { RWANDA_INITIAL_VIEW } from "./constants";

export const rwandaDistrictsMap = createMapConfig({
  id: "rwanda-districts",
  geojsonUrl: "/data/countries/rwanda/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  initialView: RWANDA_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
