/**
 * Map configuration for Canada's provinces and territories.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CANADA_INITIAL_VIEW } from "./constants";

export const canadaProvincesMap = createMapConfig({
  id: "canada-provinces",
  geojsonUrl: "/data/countries/canada/geojson/provinces.geojson",
  featureProperty: "name",

  promoteId: "pruid",

  initialView: CANADA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
