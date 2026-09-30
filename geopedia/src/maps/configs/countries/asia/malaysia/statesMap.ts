/**
 * Map configuration for Malaysia's states and federal territories.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MALAYSIA_INITIAL_VIEW } from "./constants";

export const malaysiaStatesMap = createMapConfig({
  id: "malaysia-states",
  geojsonUrl: "/data/countries/malaysia/geojson/states.geojson",

  featureProperty: "state_id",
  promoteId: "state_id",

  initialView: MALAYSIA_INITIAL_VIEW,

  hover: {
    labelProperty: "state",
  },
});
