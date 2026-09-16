import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Colombia's departments and Bogotá Capital District.
 */
export const colombiaDepartmentsMap = createMapConfig({
  id: "colombia-departments",

  geojsonUrl: "/data/countries/colombia/geojson/departments.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-74.3, 4.5],
    zoom: 4.6,
  },

  hover: {
    labelProperty: "name",
  },
});
