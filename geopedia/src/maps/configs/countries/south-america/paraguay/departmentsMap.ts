/**
 * Map configuration for Paraguay's department-level administrative divisions.
 *
 * Includes the country's 17 departments and Asunción, its capital district.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PARAGUAY_INITIAL_VIEW } from "./constants";

export const paraguayDepartmentsMap = createMapConfig({
  id: "paraguay-departments",

  geojsonUrl: "/data/countries/paraguay/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  initialView: PARAGUAY_INITIAL_VIEW,

  hover: {
    labelProperty: "department",
  },
});
