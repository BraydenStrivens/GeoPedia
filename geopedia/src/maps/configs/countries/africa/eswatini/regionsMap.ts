/**
 * Map configuration for Eswatini's regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ESWATINI_INITIAL_VIEW } from "./constants";

export const eswatiniRegionsMap = createMapConfig({
  id: "eswatini-regions",
  geojsonUrl: "/data/countries/eswatini/geojson/regions.geojson",

  featureProperty: "region",
  promoteId: "region_id",

  initialView: ESWATINI_INITIAL_VIEW,

  hover: {
    labelProperty: "region",
  },
});
