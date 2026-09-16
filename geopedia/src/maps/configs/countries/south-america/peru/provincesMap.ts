/**
 * Map configuration for Peru's second-level administrative provinces.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PERU_INITIAL_VIEW } from "./constants";

export const peruProvincesMap = createMapConfig({
  id: "peru-provinces",
  geojsonUrl: "/data/countries/peru/geojson/provinces.geojson",

  featureProperty: "province",
  promoteId: "province_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: PERU_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "province",
  },
});
