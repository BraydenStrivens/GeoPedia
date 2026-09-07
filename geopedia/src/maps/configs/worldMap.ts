/**
 * Defines the configuration for GeoPedia's interactive world-navigation map.
 *
 * The world map is used as the application's primary geographic navigation
 * interface. It provides the static geographic source, camera, background, and
 * border configuration used by `useWorldNavigationMap`.
 *
 * Country fill colors are applied dynamically by `useWorldNavigationMap`
 * according to GeoGuessr classification, while quiz availability behavior is
 * handled separately by `useWorldNavigationInteractions`.
 */

import type { MapConfig } from "../types";

/**
 * Map configuration for GeoPedia's Home world-navigation map.
 */
export const worldMap: MapConfig = {
  id: "world-map",

  geojsonUrl:
    "/data/global/countries/geojson/world-countries.geojson",

  featureProperty: "name",

  style: {
    type: "minimal",

    /*
     * Uses a very light cool blue-gray so the map reads as geographic rather
     * than as another neutral UI panel while remaining visually understated.
     */
    backgroundColor: "#e8f1f5",
  },

  /*
   * Promotes each country's ISO alpha-3 property to MapLibre's feature ID.
   *
   * This lets world-navigation hooks apply independent feature state for
   * GeoGuessr classification, quiz availability, and hover highlighting.
   */
  promoteId: "iso_a3",

  initialView: {
    center: [0, 20],
    zoom: 1.5,
  },

  layers: {
    /*
     * This neutral color acts as the fallback fill supplied when the geographic
     * layer is created. `useWorldNavigationMap` replaces it with a feature-state
     * expression that distinguishes GeoGuessr from other countries.
     */
    fill: {
      color: "#cbd5e1",
      opacity: 1,
    },

    /*
     * Country borders stay slightly darker than either base fill so adjacent
     * countries remain distinguishable without creating harsh black outlines.
     */
    borders: {
      color: "#94a3b8",
      width: 1,
    },
  },

  /*
   * Hover remains enabled because the shared geographic layer configuration
   * expects a hover definition. The world-navigation hook replaces the final
   * fill-color expression with classification-aware hover colors.
   */
  hover: {
    enabled: true,
    color: "#7dd3fc",
    labelProperty: "name",
  },
};
