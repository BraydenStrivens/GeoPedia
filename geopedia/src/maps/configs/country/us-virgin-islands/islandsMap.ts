import { createMapConfig } from "../../createMapConfig";

/**
 * Map configuration for the U.S. Virgin Islands' islands.
 */
export const usVirginIslandsIslandsMap = createMapConfig({
  id: "us-virgin-islands-islands",

  geojsonUrl:
    "/data/countries/us-virgin-islands/geojson/islands.geojson",

  featureProperty: "name",
  promoteId: "island_id",

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
