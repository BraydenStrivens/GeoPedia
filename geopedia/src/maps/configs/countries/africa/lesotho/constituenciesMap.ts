/**
 * Map configuration for Lesotho's constituencies.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { LESOTHO_INITIAL_VIEW } from "./constants";

export const lesothoConstituenciesMap = createMapConfig({
  id: "lesotho-constituencies",
  geojsonUrl:
    "/data/countries/lesotho/geojson/constituencies.geojson",

  featureProperty: "constituency",
  promoteId: "constituency_id",

  initialView: LESOTHO_INITIAL_VIEW,

  hover: {
    labelProperty: "constituency",
  },
});
