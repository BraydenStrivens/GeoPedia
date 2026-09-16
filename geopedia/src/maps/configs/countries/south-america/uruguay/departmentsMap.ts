import { createMapConfig } from "@/maps/configs/createMapConfig";

export const uruguayDepartmentsMap = createMapConfig({
  id: "uruguay-departments",

  geojsonUrl: "/data/countries/uruguay/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  initialView: {
    center: [-56.0, -32.8],
    zoom: 5.5,
  },

  hover: {
    labelProperty: "department",
  },

  style: {
    type: "maptiler",
  },
});
