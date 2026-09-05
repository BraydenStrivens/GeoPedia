/**
 * Map configuration used by global quizzes whose answers are countries or
 * territories on the world map, and who's labels should not be displayed on the
 * base map.
 *
 * The configuration connects GeoPedia's reusable quiz-map system to
 * world-countries.geojson. Individual global quizzes can reuse this map when
 * they ask the player to identify a country by selecting its geographic
 * feature.
 */

import type { MapConfig } from "@/maps/types";

export const worldCountryCapitalsMap: MapConfig = {
  id: "world-country-capitals",
  geojsonUrl:
    "/data/global/countries/geojson/world-countries.geojson",

  featureProperty: "name",

  /*
   * Use the same MapTiler/base-map style as the existing world navigation map.
   *
   * Replace this value with the exact `style` object from your existing world
   * navigation MapConfig if its style currently differs.
   */
  style: {
    type: "maptiler",
  },

  promoteId: "iso_a3",

  baseMapLayers: {
    countryLabels: true,
    subdivisionLabels: false,
    townLabels: false,

    countryBorders: true,
    subdivisionBorders: true,
  },

  answerLabels: {
    densityThreshold: 150,
    initialMaxLabels: 75,
    labelsPerZoom: 75,
  },

  initialView: {
    center: [0, 20],
    zoom: 1.25,
  },

  layers: {
    fill: {
      color: "#969696",
      opacity: 0.35,
    },

    borders: {
      color: "#000000",
      width: 0.8,
    },
  },

  hover: {
    enabled: true,
    color: "#4e4e4e",
    labelProperty: "fullName",
  },
};
