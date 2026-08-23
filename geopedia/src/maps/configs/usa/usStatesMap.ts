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

import type { MapConfig } from "../../types";

/**
 * Shared map configuration for quizzes and features using US state
 * boundaries.
 */
export const usStatesMap: MapConfig = {
  id: "us-states",
  geojsonUrl: "/data/us-states.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  /*
   * Promotes each state's abbreviation to MapLibre's feature ID so
   * feature-state operations such as hover highlighting can reliably
   * target individual states.
   */
  promoteId: "abbreviation",

  initialView: {
    center: [-98.5, 39.8],
    zoom: 3.5,
  },

  layers: {
    fill: {
      color: "#969696",
      opacity: 0.35,
    },

    borders: {
      color: "#000000",
      width: 1.5,
    },
  },

  hover: {
    enabled: true,
    color: "#4e4e4e",
    labelProperty: "name",
  },
};
