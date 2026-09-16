/**
 * Map configuration for Peru's third-level administrative districts.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PERU_INITIAL_VIEW } from "./constants";

export const peruDistrictsMap = createMapConfig({
  id: "peru-districts",
  geojsonUrl: "/data/countries/peru/geojson/districts.geojson",

  featureProperty: "district",
  promoteId: "district_id",

  answerLabels: {
    densityThreshold: 300,
    initialMaxLabels: 100,
    labelsPerZoom: 200,
  },

  initialView: PERU_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "district",
  },
});
