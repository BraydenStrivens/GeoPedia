/**
 * Map configuration for Bolivia's geographic landline area-code regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BOLIVIA_INITIAL_VIEW } from "./constants";

export const boliviaAreaCodesMap = createMapConfig({
  id: "bolivia-area-codes",

  geojsonUrl: "/data/countries/bolivia/geojson/area-codes.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  initialView: BOLIVIA_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code",
  },
});
