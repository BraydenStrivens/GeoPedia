/**
 * Map configuration used by global quizzes whose answers are countries or
 * territories on the world map.
 *
 * The configuration connects GeoPedia's reusable quiz-map system to
 * world-countries.geojson. Individual global quizzes can reuse this map when
 * they ask the player to identify a country by selecting its geographic
 * feature.
 */

import { createMapConfig } from "../createMapConfig";

/**
 * Shared world-country map used by global country-identification quizzes.
 *
 * Country features are promoted by ISO-A3 so MapLibre feature state, quiz
 * coloring, manual groups, hover behavior, and answer labels all refer to the
 * same stable geographic identifier.
 */
export const worldCountriesMap = createMapConfig({
  id: "world-countries",
  geojsonUrl:
    "/data/global/countries/geojson/world-countries.geojson",

  featureProperty: "name",

  promoteId: "iso_a3",

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
    borders: {
      width: 0.8,
    },
  },

  hover: {
    labelProperty: "fullName",
  },
});
