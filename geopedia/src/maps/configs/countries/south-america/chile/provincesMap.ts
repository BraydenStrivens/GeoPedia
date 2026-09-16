/**
 * Map configuration for Chile's second-level administrative provinces.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CHILE_INITIAL_VIEW } from "./constants";

export const chileProvincesMap = createMapConfig({
  id: "chile-provinces",

  geojsonUrl: "/data/countries/chile/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: CHILE_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
