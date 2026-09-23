/**
 * Map configuration for Tunisia's wilayat (governorates).
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TUNISIA_INITIAL_VIEW } from "./constants";

export const tunisiaGovernoratesMap = createMapConfig({
  id: "tunisia-governorates",

  geojsonUrl: "/data/countries/tunisia/geojson/governorates.geojson",

  featureProperty: "governorate_id",
  promoteId: "governorate_id",

  initialView: TUNISIA_INITIAL_VIEW,

  hover: {
    labelProperty: "governorate",
  },
});
