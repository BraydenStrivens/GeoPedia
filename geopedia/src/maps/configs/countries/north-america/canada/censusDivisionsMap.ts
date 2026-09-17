/**
 * Map configuration for Canada's census divisions.
 */

import { createMapConfig } from "../../../createMapConfig";
import { CANADA_INITIAL_VIEW } from "./constants";

export const canadaCensusDivisionsMap = createMapConfig({
  id: "canada-census-divisions",

  geojsonUrl:
    "/data/countries/canada/geojson/census-divisions.geojson",

  featureProperty: "name",

  promoteId: "cduid",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: CANADA_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
