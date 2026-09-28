/**
 * Map configuration for the Philippines' municipalities and cities.
 *
 * Features use the canonical municipality_city_id property for map identity
 * and answers. Answer labels are throttled because the map contains more than
 * 1,600 subdivisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PHILIPPINES_INITIAL_VIEW } from "./constants";

export const philippinesMunicipalitiesCitiesMap = createMapConfig({
  id: "philippines-municipalities-cities",
  geojsonUrl:
    "/data/countries/philippines/geojson/municipalities-cities.geojson",

  featureProperty: "municipality_city_id",
  promoteId: "municipality_city_id",

  initialView: PHILIPPINES_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 150,
    initialMaxLabels: 75,
    labelsPerZoom: 125,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "municipality_city",
  },
});
