/**
 * Map configuration for Colombia's first-level administrative departments.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { COLOMBIA_INITIAL_VIEW } from "./constants";

export const colombiaDepartmentsMap = createMapConfig({
  id: "colombia-departments",

  geojsonUrl: "/data/countries/colombia/geojson/departments.geojson",

  featureProperty: "name",
  promoteId: "id",

  initialView: COLOMBIA_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
