/**
 * Map configuration for Uruguay's municipalities.
 *
 * Municipality boundaries do not cover the entire country because some areas
 * of Uruguay are not incorporated into a municipality.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { URUGUAY_INITIAL_VIEW } from "./constants";

export const uruguayMunicipalitiesMap = createMapConfig({
  id: "uruguay-municipalities",

  geojsonUrl:
    "/data/countries/uruguay/geojson/municipalities.geojson",

  featureProperty: "municipality_id",
  promoteId: "municipality_id",

  initialView: URUGUAY_INITIAL_VIEW,

  hover: {
    labelProperty: "municipality",
  },
});
