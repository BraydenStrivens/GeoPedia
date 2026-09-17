/**
 * Map configuration for Ecuador's geographic fixed-line telephone area-code
 * regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ECUADOR_INITIAL_VIEW } from "./constants";

export const ecuadorAreaCodesMap = createMapConfig({
  id: "ecuador-area-codes",
  geojsonUrl: "/data/countries/ecuador/geojson/area-codes.geojson",

  featureProperty: "area_code",
  promoteId: "area_code_id",

  initialView: ECUADOR_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
