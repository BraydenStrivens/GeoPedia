/**
 * Map configuration for Vietnam's pre-reform commune-level administrative
 * units.
 *
 * Answer labels are limited at wider zoom levels because the layer contains
 * more than 10,000 features.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { VIETNAM_INITIAL_VIEW } from "./constants";

export const vietnamPreReformCommunesMap = createMapConfig({
  id: "vietnam-pre-reform-communes",
  geojsonUrl:
    "/data/countries/vietnam/geojson/pre-reform-communes.geojson",

  featureProperty: "commune_id",
  promoteId: "commune_id",

  initialView: VIETNAM_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "commune",
  },
});
