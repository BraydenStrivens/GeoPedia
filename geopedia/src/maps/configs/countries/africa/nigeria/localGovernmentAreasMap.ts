/**
 * Map configuration for Nigeria's Local Government Areas.
 *
 * Features use the canonical lga_id property for map identity and answers.
 * Answer labels are throttled because the map contains 774 subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { NIGERIA_INITIAL_VIEW } from "./constants";

export const nigeriaLocalGovernmentAreasMap = createMapConfig({
  id: "nigeria-local-government-areas",
  geojsonUrl:
    "/data/countries/nigeria/geojson/local-government-areas.geojson",

  featureProperty: "lga_id",
  promoteId: "lga_id",

  initialView: NIGERIA_INITIAL_VIEW,

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
    labelProperty: "lga",
  },
});
