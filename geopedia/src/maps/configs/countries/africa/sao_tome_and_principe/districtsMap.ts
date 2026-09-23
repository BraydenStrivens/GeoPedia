/**
 * Map configuration for São Tomé and Príncipe's seven districts.
 *
 * Features use the canonical district_id property for map identity and
 * quiz answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SAO_TOME_AND_PRINCIPE_INITIAL_VIEW } from "./constants";

export const saoTomeAndPrincipeDistrictsMap = createMapConfig({
  id: "sao-tome-and-principe-districts",
  geojsonUrl:
    "/data/countries/sao_tome_and_principe/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  initialView: SAO_TOME_AND_PRINCIPE_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
