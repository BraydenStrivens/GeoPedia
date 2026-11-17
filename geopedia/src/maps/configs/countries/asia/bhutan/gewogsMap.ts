/**
 * Map configuration for Bhutan's 205 gewogs.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BHUTAN_INITIAL_VIEW } from "./constants";

export const bhutanGewogsMap = createMapConfig({
  id: "bhutan-gewogs",
  geojsonUrl: "/data/countries/bhutan/geojson/bhutan_adm2.geojson",

  featureProperty: "name",
  promoteId: "admin_id",

  initialView: BHUTAN_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "name",
  },
});
