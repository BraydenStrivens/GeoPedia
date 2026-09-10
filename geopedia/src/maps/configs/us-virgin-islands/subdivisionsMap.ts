import { createMapConfig } from "../createMapConfig";

/**
 * Map configuration for the U.S. Virgin Islands' subdivisions.
 */
export const usVirginIslandsSubdivisionsMap = createMapConfig({
  id: "us-virgin-islands-subdivisions",

  geojsonUrl:
    "/data/countries/us-virgin-islands/geojson/subdivisions.geojson",

  featureProperty: "name",
  promoteId: "subdivision_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-64.78, 18.05],
    zoom: 8,
  },

  hover: {
    labelProperty: "name",
  },
});
