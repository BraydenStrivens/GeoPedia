/**
 * Map configuration for Indonesia's fourth-level administrative villages.
 *
 * Answer-label density is heavily limited because this map contains more than
 * 80,000 geographic features.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaVillagesMap = createMapConfig({
  id: "indonesia-villages",

  geojsonUrl: "/data/countries/indonesia/geojson/villages.geojson",

  featureProperty: "village_id",
  promoteId: "village_id",

  initialView: INDONESIA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 150,
    initialMaxLabels: 50,
    labelsPerZoom: 100,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "village",
  },
});
