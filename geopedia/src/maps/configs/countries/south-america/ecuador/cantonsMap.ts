/**
 * Map configuration for Ecuador's 221 cantons.
 *
 * Each feature uses the official ADM2 PCODE as its stable feature ID.
 * Province information is retained on each feature for quiz grouping.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ECUADOR_INITIAL_VIEW } from "./constants";

export const ecuadorCantonsMap = createMapConfig({
  id: "ecuador-cantons",

  geojsonUrl: "/data/countries/ecuador/geojson/cantons.geojson",

  featureProperty: "canton",
  promoteId: "canton_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: ECUADOR_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "canton",
  },
});
