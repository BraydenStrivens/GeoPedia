import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Brazil's states and Federal District.
 */
export const brazilStatesMap = createMapConfig({
  id: "brazil-states",

  geojsonUrl: "/data/countries/brazil/geojson/states.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-52.5, -14.5],
    zoom: 3.2,
  },

  hover: {
    labelProperty: "name",
  },
});
