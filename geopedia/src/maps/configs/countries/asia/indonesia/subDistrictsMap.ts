/**
 * Map configuration for Indonesia's third-level administrative sub-districts.
 *
 * Answer-label density is limited because this map contains more than
 * 7,000 geographic features.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaSubDistrictsMap = createMapConfig({
  id: "indonesia-sub-districts",

  geojsonUrl:
    "/data/countries/indonesia/geojson/sub-districts.geojson",

  featureProperty: "sub_district_id",
  promoteId: "sub_district_id",

  initialView: INDONESIA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 150,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "sub_district",
  },
});
