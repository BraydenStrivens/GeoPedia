/**
 * Map configuration for United States 1-digit ZIP-code prefix regions.
 */

import { createMapConfig } from "../../../createMapConfig";
import { USA_INITIAL_VIEW } from "./constants";

export const usZip1Map = createMapConfig({
  id: "us-zip-1",
  geojsonUrl: "/data/countries/usa/geojson/zip-1.geojson",

  featureProperty: "zip",

  promoteId: "id",

  initialView: USA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "zip",
  },
});
