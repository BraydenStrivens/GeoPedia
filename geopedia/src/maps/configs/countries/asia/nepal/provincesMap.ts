/**
 * Map configuration for Nepal's 7 provinces (ADM1).
 *
 * Uses province administrative codes as stable feature identifiers
 * and English province names as hover labels.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { NEPAL_INITIAL_VIEW } from "./constants";

export const nepalProvincesMap = createMapConfig({
  id: "nepal-provinces",
  geojsonUrl: "/data/countries/nepal/geojson/nepal_adm1.geojson",
  featureProperty: "name",

  promoteId: "admin_id",

  initialView: NEPAL_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
