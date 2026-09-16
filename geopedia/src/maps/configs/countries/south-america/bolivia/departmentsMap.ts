/**
 * Map configuration for Bolivia's first-level administrative departments.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BOLIVIA_INITIAL_VIEW } from "./constants";

export const boliviaDepartmentsMap = createMapConfig({
  id: "bolivia-departments",

  geojsonUrl: "/data/countries/bolivia/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  initialView: BOLIVIA_INITIAL_VIEW,

  hover: {
    labelProperty: "department",
  },
});
