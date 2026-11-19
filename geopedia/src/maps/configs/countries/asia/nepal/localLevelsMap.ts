/**
 * Map configuration for Nepal's 753 local levels (ADM3).
 *
 * Includes rural municipalities, municipalities, sub-metropolitan
 * cities, and metropolitan cities.
 *
 * Supports grouping by province, district, and local level type.
 * Uses density-based answer labels to reduce visual clutter at
 * lower zoom levels.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { NEPAL_INITIAL_VIEW } from "./constants";

export const nepalLocalLevelsMap = createMapConfig({
  id: "nepal-local-levels",
  geojsonUrl: "/data/countries/nepal/geojson/nepal_adm3.geojson",
  featureProperty: "name",

  promoteId: "admin_id",

  initialView: NEPAL_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },
});
