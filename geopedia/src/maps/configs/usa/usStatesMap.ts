/**
 * Defines the shared map configuration for United States state geography.
 *
 * This map displays the 50 US states using the US states GeoJSON dataset.
 * It is designed to be reusable across quizzes that use state boundaries,
 * such as the US States and US State Abbreviations quizzes.
 *
 * Quiz-specific information, including which GeoJSON property represents
 * the answer, is defined by each quiz rather than by this map.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Shared map configuration for quizzes and features using US state
 * boundaries.
 */
export const usStatesMap = createMapConfig({
  id: "us-states",
  geojsonUrl: "/data/countries/usa/geojson/states.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "abbreviation",

  initialView: {
    center: [-98.5, 39.8],
    zoom: 3.5,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
