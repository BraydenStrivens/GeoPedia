import { createMapConfig } from "../../createMapConfig";

/**
 * Map configuration for Puerto Rico's municipalities.
 */
export const puertoRicoMunicipalitiesMap = createMapConfig({
  id: "puerto-rico-municipalities",

  geojsonUrl:
    "/data/countries/puerto-rico/geojson/municipalities.geojson",

  featureProperty: "name",
  promoteId: "municipality_id",

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
