/**
 * Map configuration for Tunisia's geographic landline area codes.
 *
 * The map dissolves Tunisia's governorates into eight geographic landline
 * regions. Grand Tunis accepts codes 70, 71, and 79, while the remaining
 * geographic regions each accept one area code.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TUNISIA_INITIAL_VIEW } from "./constants";

export const tunisiaAreaCodesMap = createMapConfig({
  id: "tunisia-area-codes",

  geojsonUrl: "/data/countries/tunisia/geojson/area-codes.geojson",

  featureProperty: "area_code_id",
  promoteId: "area_code_id",

  initialView: TUNISIA_INITIAL_VIEW,

  hover: {
    labelProperty: "governorates",
  },
});
