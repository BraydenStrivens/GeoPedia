/**
 * Map configuration for Rwanda's intara (provinces) and City of Kigali.
 *
 * Features use the canonical province_id property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { RWANDA_INITIAL_VIEW } from "./constants";

export const rwandaProvincesMap = createMapConfig({
  id: "rwanda-provinces",
  geojsonUrl: "/data/countries/rwanda/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: RWANDA_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
