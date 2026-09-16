/**
 * Map configuration for Chile's geographic landline area-code regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CHILE_INITIAL_VIEW } from "./constants";

export const chileAreaCodesMap = createMapConfig({
  id: "chile-area-codes",

  geojsonUrl: "/data/countries/chile/geojson/area-codes.geojson",

  featureProperty: "area_code_id",
  promoteId: "area_code_id",

  initialView: CHILE_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code",
  },
});
