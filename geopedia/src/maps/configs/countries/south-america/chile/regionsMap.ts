/**
 * Map configuration for Chile's first-level administrative regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CHILE_INITIAL_VIEW } from "./constants";

export const chileRegionsMap = createMapConfig({
  id: "chile-regions",

  geojsonUrl: "/data/countries/chile/geojson/regions.geojson",

  featureProperty: "region_id",
  promoteId: "region_id",

  initialView: CHILE_INITIAL_VIEW,

  hover: {
    labelProperty: "region",
  },
});
