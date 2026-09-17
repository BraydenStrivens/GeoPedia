/**
 * Map configuration for United States states.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { USA_INITIAL_VIEW } from "./constants";

export const usStatesMap = createMapConfig({
  id: "us-states",
  geojsonUrl: "/data/countries/usa/geojson/states.geojson",
  featureProperty: "name",

  promoteId: "abbreviation",

  initialView: USA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
