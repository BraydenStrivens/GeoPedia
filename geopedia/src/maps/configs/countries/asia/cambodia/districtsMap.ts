/**
 * Map configuration for Cambodia's second-level administrative divisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CAMBODIA_INITIAL_VIEW } from "./constants";

export const cambodiaDistrictsMap = createMapConfig({
  id: "cambodia-districts",
  geojsonUrl: "/data/countries/cambodia/geojson/districts.geojson",

  featureProperty: "district_id",
  promoteId: "district_id",

  initialView: CAMBODIA_INITIAL_VIEW,

  hover: {
    labelProperty: "district",
  },
});
