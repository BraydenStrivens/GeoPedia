/**
 * Map configuration for United States counties and county equivalents.
 *
 * Counties are identified by their Census GEOID.
 */

import { createMapConfig } from "../../../createMapConfig";
import { USA_INITIAL_VIEW } from "./constants";

export const usCountiesMap = createMapConfig({
  id: "us-counties",
  geojsonUrl: "/data/countries/usa/geojson/counties.geojson",

  featureProperty: "geoid",

  promoteId: "geoid",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: USA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "fullName",
  },
});
