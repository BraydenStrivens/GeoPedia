/**
 * Defines the configuration for GeoPedia's interactive world map.
 *
 * The world map is used as the application's primary geographic
 * navigation interface. It displays countries from the countries GeoJSON
 * dataset, highlights countries when hovered, displays their names, and
 * navigates to the corresponding country page when clicked.
 *
 * Unlike country-specific maps, this map is intended for navigation rather
 * than running a quiz.
 */

import type { MapConfig } from "../types";

/**
 * Map configuration for the world country map.
 */
export const worldMap: MapConfig = {
  id: "world-map",
  geojsonUrl: "/data/geojson/world/countries.geojson",

  featureProperty: "name",

  style: {
    type: "minimal",
    backgroundColor: "#d1d5db",
  },

  /*
   * Promotes each country's ISO alpha-3 property to MapLibre's feature ID
   * so feature-state operations such as hover highlighting can reliably
   * target individual countries.
   */
  promoteId: "iso_a3",

  initialView: {
    center: [0, 20],
    zoom: 1.5,
  },

  layers: {
    fill: {
      color: "#969696",
      opacity: 0.35,
    },

    borders: {
      color: "#000000",
      width: 1,
    },
  },

  hover: {
    enabled: true,
    color: "#4e4e4e",
    labelProperty: "name",
  },
};
