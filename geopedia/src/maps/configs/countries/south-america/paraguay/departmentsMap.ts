import { createMapConfig } from "@/maps/configs/createMapConfig";

export const paraguayDepartmentsMap = createMapConfig({
  id: "paraguay-departments",

  geojsonUrl: "/data/countries/paraguay/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-58.3, -23.4],
    zoom: 4.9,
  },

  hover: {
    labelProperty: "department",
  },
});
