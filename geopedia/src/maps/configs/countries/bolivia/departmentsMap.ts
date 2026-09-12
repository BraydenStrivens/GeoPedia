import { createMapConfig } from "@/maps/configs/createMapConfig";

export const boliviaDepartmentsMap = createMapConfig({
  id: "bolivia-departments",

  geojsonUrl: "/data/countries/bolivia/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-64.7, -16.7],
    zoom: 4.6,
  },

  hover: {
    labelProperty: "department",
  },
});
