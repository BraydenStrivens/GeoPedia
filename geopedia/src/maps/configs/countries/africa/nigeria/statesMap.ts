/**
 * Map configuration for Nigeria's states and Federal Capital Territory.
 *
 * Features use the canonical state_id property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { NIGERIA_INITIAL_VIEW } from "./constants";

export const nigeriaStatesMap = createMapConfig({
  id: "nigeria-states",
  geojsonUrl: "/data/countries/nigeria/geojson/states.geojson",

  featureProperty: "state_id",
  promoteId: "state_id",

  initialView: NIGERIA_INITIAL_VIEW,

  hover: {
    labelProperty: "state",
  },
});
