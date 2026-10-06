/**
 * Map configuration for Cambodia's third-level administrative communes.
 *
 * Answer labels are hidden at lower zoom levels because of the high
 * density of commune features.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CAMBODIA_INITIAL_VIEW } from "./constants";

export const cambodiaCommunesMap = createMapConfig({
  id: "cambodia-communes",
  geojsonUrl: "/data/countries/cambodia/geojson/communes.geojson",

  featureProperty: "commune_id",
  promoteId: "commune_id",

  initialView: CAMBODIA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "commune",
  },
});
