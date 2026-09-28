/**
 * Map configuration for Indonesia's second-level regencies and cities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaRegenciesMap = createMapConfig({
  id: "indonesia-regencies",

  geojsonUrl: "/data/countries/indonesia/geojson/regencies.geojson",

  featureProperty: "regency_id",
  promoteId: "regency_id",

  initialView: INDONESIA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 150,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "regency",
  },
});
