/**
 * Map configuration for the Philippines' provinces and province-level units.
 *
 * Features use the canonical province_id property for map identity and
 * answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PHILIPPINES_INITIAL_VIEW } from "./constants";

export const philippinesProvincesMap = createMapConfig({
  id: "philippines-provinces",
  geojsonUrl: "/data/countries/philippines/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: PHILIPPINES_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
