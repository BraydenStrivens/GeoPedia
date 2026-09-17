/**
 * Map configuration for Brazil's states and Federal District.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BRAZIL_INITIAL_VIEW } from "./constants";

export const brazilStatesMap = createMapConfig({
  id: "brazil-states",

  geojsonUrl: "/data/countries/brazil/geojson/states.geojson",

  featureProperty: "name",
  promoteId: "id",

  initialView: BRAZIL_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
