/**
 * Map configuration for Nepal's 77 districts (ADM2).
 *
 * Uses district administrative codes as stable feature identifiers.
 * District boundaries include parent province properties for
 * administrative grouping.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { NEPAL_INITIAL_VIEW } from "./constants";

export const nepalDistrictsMap = createMapConfig({
  id: "nepal-districts",
  geojsonUrl: "/data/countries/nepal/geojson/nepal_adm2.geojson",
  featureProperty: "name",

  promoteId: "admin_id",

  initialView: NEPAL_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
