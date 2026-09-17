/**
 * Map configuration for Mexico's states and federal entity.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MEXICO_INITIAL_VIEW } from "./constants";

export const mexicoStatesMap = createMapConfig({
  id: "mexico-states",
  geojsonUrl: "/data/countries/mexico/geojson/states.geojson",
  featureProperty: "name",

  promoteId: "state_id",

  initialView: MEXICO_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
