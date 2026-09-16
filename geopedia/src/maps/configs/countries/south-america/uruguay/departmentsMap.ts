/**
 * Map configuration for Uruguay's first-level administrative departments.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { URUGUAY_INITIAL_VIEW } from "./constants";

export const uruguayDepartmentsMap = createMapConfig({
  id: "uruguay-departments",

  geojsonUrl: "/data/countries/uruguay/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  initialView: URUGUAY_INITIAL_VIEW,

  hover: {
    labelProperty: "department",
  },
});
