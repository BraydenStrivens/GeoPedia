/**
 * Map configuration for Malaysia's third-level administrative sub-districts.
 *
 * Answer-label density is limited because the map contains more than 1,800
 * administrative features.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MALAYSIA_INITIAL_VIEW } from "./constants";

export const malaysiaSubDistrictsMap = createMapConfig({
  id: "malaysia-sub-districts",
  geojsonUrl:
    "/data/countries/malaysia/geojson/sub-districts.geojson",

  featureProperty: "sub_district_id",
  promoteId: "sub_district_id",

  initialView: MALAYSIA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "sub_district",
  },
});
