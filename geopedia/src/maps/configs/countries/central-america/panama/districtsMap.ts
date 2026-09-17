/**
 * Map configuration for Panama's district-level administrative boundaries.
 *
 * The processed GeoJSON contains 82 structural features, including Kuna
 * Yala's `1000` hierarchy placeholder. Quiz configuration determines which
 * of those features are included as questions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PANAMA_INITIAL_VIEW } from "./constants";

export const panamaDistrictsMap = createMapConfig({
  id: "panama-districts",

  geojsonUrl: "/data/countries/panama/geojson/districts.geojson",

  featureProperty: "name",
  promoteId: "id",

  initialView: PANAMA_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
