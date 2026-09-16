/**
 * Map configuration for Argentina's second-level administrative divisions.
 *
 * Includes departments, Buenos Aires Province's partidos, and the communes
 * of the Autonomous City of Buenos Aires.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ARGENTINA_INITIAL_VIEW } from "./constants";

export const argentinaDepartmentsMap = createMapConfig({
  id: "argentina-departments",

  geojsonUrl: "/data/countries/argentina/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: ARGENTINA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "department",
  },
});
