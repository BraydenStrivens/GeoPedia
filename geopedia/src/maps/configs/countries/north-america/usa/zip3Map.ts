/**
 * Map configuration for United States 3-digit ZIP-code prefix regions.
 */

import { createMapConfig } from "../../../createMapConfig";
import { USA_INITIAL_VIEW } from "./constants";

export const usZip3Map = createMapConfig({
  id: "us-zip-3",
  geojsonUrl: "/data/countries/usa/geojson/zip-3.geojson",

  featureProperty: "zip",

  promoteId: "id",

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
    labelProperty: "zip",
  },
});
