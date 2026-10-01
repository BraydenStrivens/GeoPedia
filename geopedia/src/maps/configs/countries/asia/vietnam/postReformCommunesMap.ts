/**
 * Map configuration for Vietnam's post-reform commune-level administrative
 * units.
 *
 * Answer labels are limited at wider zoom levels because the layer contains
 * more than 3,000 features.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { VIETNAM_INITIAL_VIEW } from "./constants";

export const vietnamPostReformCommunesMap = createMapConfig({
  id: "vietnam-post-reform-communes",
  geojsonUrl:
    "/data/countries/vietnam/geojson/post-reform-communes.geojson",

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
