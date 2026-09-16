/**
 * Map configuration for Chile's third-level administrative communes.
 *
 * Commune maps use reduced border width and answer-label throttling because
 * Chile contains a large number of relatively small geographic features.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CHILE_INITIAL_VIEW } from "./constants";

export const chileCommunesMap = createMapConfig({
  id: "chile-communes",

  geojsonUrl: "/data/countries/chile/geojson/communes.geojson",

  featureProperty: "commune_id",
  promoteId: "commune_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: CHILE_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "commune",
  },
});
