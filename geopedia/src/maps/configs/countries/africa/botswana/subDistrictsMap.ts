/**
 * Map configuration for Botswana's sub-districts.
 *
 * Features use the canonical sub_district_id property for map identity and
 * answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BOTSWANA_INITIAL_VIEW } from "./constants";

export const botswanaSubDistrictsMap = createMapConfig({
  id: "botswana-sub-districts",
  geojsonUrl:
    "/data/countries/botswana/geojson/sub-districts.geojson",

  featureProperty: "sub_district_id",
  promoteId: "sub_district_id",

  initialView: BOTSWANA_INITIAL_VIEW,

  hover: {
    labelProperty: "sub_district",
  },
});
