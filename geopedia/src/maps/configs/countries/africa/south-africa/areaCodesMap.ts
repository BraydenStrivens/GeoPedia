/**
 * Map configuration for South Africa's geographic telephone area codes.
 *
 * The runtime geometry is derived from municipal wards classified using
 * geographic landline observations from OpenStreetMap.
 *
 * 010 is an alternative Johannesburg code and shares the geographic feature
 * represented by 011. Runtime features expose accepted area codes as arrays
 * so the shared Johannesburg feature can accept both 010 and 011.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_AFRICA_INITIAL_VIEW } from "./constants";

export const southAfricaAreaCodesMap = createMapConfig({
  id: "south-africa-area-codes",
  geojsonUrl:
    "/data/countries/south-africa/geojson/area-codes.geojson",
  featureProperty: "area_codes",
  promoteId: "area_code_id",
  initialView: SOUTH_AFRICA_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code_label",
  },
});
