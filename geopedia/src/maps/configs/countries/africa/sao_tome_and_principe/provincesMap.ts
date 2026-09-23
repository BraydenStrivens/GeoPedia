/**
 * Map configuration for São Tomé and Príncipe's two provinces.
 *
 * Features use the canonical province_id property for map identity and
 * quiz answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SAO_TOME_AND_PRINCIPE_INITIAL_VIEW } from "./constants";

export const saoTomeAndPrincipeProvincesMap = createMapConfig({
  id: "sao-tome-and-principe-provinces",
  geojsonUrl:
    "/data/countries/sao_tome_and_principe/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: SAO_TOME_AND_PRINCIPE_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
