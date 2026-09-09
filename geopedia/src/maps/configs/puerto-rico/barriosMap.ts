import { createMapConfig } from "../createMapConfig";

/**
 * Map configuration for Puerto Rico's barrios.
 */
export const puertoRicoBarriosMap = createMapConfig({
  id: "puerto-rico-barrios",

  geojsonUrl: "/data/countries/puerto-rico/geojson/barrios.geojson",

  featureProperty: "name",
  promoteId: "barrio_id",

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-66.45, 18.22],
    zoom: 8,
  },

  hover: {
    labelProperty: "name",
  },
});
