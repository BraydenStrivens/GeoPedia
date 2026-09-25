/**
 * Map configuration for South Africa's provinces.
 *
 * Features use the canonical province_id property for map identity and
 * answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaProvincesMap = createMapConfig({
  id: "south-africa-provinces",
  geojsonUrl:
    "/data/countries/south-africa/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
