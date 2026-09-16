import { createMapConfig } from "@/maps/configs/createMapConfig";

export const argentinaDepartmentsMap = createMapConfig({
  id: "argentina-departments",

  geojsonUrl: "/data/countries/argentina/geojson/departments.geojson",

  featureProperty: "department_id",
  promoteId: "department_id",

  style: {
    type: "maptiler",
  },

  answerLabels: {
    densityThreshold: 200,
    initialMaxLabels: 100,
    labelsPerZoom: 150,
  },

  initialView: {
    center: [-64.5, -38.5],
    zoom: 3.4,
  },

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "department",
  },
});
