/**
 * Map configuration for Kenya's wards.
 *
 * Features use the canonical ward_id property for map identity and answers.
 * Answer labels are throttled because the map contains 1,452 subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { KENYA_INITIAL_VIEW } from "./constants";

export const kenyaWardsMap = createMapConfig({
  id: "kenya-wards",
  geojsonUrl: "/data/countries/kenya/geojson/wards.geojson",

  featureProperty: "ward_id",
  promoteId: "ward_id",

  initialView: KENYA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 75,
    labelsPerZoom: 125,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "ward",
  },
});
