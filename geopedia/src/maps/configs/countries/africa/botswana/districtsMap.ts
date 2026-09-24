/**
 * Map configuration for Botswana's districts.
 *
 * Features use the canonical district_id property for map identity and
 * answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BOTSWANA_INITIAL_VIEW } from "./constants";

export const botswanaDistrictsMap = createMapConfig({
  id: "botswana-districts",
  geojsonUrl: "/data/countries/botswana/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  initialView: BOTSWANA_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
