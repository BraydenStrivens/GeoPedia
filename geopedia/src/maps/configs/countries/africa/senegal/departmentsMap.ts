/**
 * Map configuration for Senegal's second-level administrative departments.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SENEGAL_INITIAL_VIEW } from "./constants";

export const senegalDepartmentsMap = createMapConfig({
  id: "senegal-departments",

  geojsonUrl: "/data/countries/senegal/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  initialView: SENEGAL_INITIAL_VIEW,

  hover: {
    labelProperty: "department",
  },
});
