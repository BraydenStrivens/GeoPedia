/**
 * Map configuration for United States 2-digit ZIP-code prefix regions.
 */

import { createMapConfig } from "../../../createMapConfig";
import { USA_INITIAL_VIEW } from "./constants";

export const usZip2Map = createMapConfig({
  id: "us-zip-2",
  geojsonUrl: "/data/countries/usa/geojson/zip-2.geojson",

  featureProperty: "zip",

  promoteId: "id",

  initialView: USA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.25,
    },
  },

  hover: {
    labelProperty: "zip",
  },
});
