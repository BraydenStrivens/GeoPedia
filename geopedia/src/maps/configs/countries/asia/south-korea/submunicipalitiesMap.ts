/**
 * Map configuration for South Korea's submunicipalities.
 *
 * Features use submunicipality_id as their stable map identity. Answer labels
 * are heavily throttled because the map contains 3,504 submunicipalities.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_KOREA_INITIAL_VIEW } from "./constants";

export const southKoreaSubmunicipalitiesMap = createMapConfig({
  id: "south-korea-submunicipalities",
  geojsonUrl:
    "/data/countries/south-korea/geojson/submunicipalities.geojson",

  featureProperty: "submunicipality",
  promoteId: "submunicipality_id",

  initialView: SOUTH_KOREA_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 100,
    labelsPerZoom: 100,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "submunicipality",
  },
});
