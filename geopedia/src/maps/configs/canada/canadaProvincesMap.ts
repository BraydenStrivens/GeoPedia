/**
 * Defines the shared map configuration for Canadian province and territory
 * geography.
 *
 * This map displays Canada's 10 provinces and 3 territories using the
 * processed Statistics Canada province and territory GeoJSON dataset.
 * It is designed to be reusable across quizzes that use these boundaries,
 * such as the Canada Provinces and Territories and Canada Province and
 * Territory Flags quizzes.
 *
 * Quiz-specific information, including which GeoJSON property represents
 * the answer, is defined by each quiz rather than by this map.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Shared map configuration for quizzes and features using Canadian province
 * and territory boundaries.
 */
export const canadaProvincesMap = createMapConfig({
  id: "canada-provinces",
  geojsonUrl: "/data/countries/canada/geojson/provinces.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "pruid",

  initialView: {
    center: [-96, 61],
    zoom: 2.4,
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
