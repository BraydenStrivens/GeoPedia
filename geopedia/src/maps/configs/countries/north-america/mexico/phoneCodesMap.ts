/**
 * Map configuration for Mexico's geographic telephone area codes.
 *
 * Individual geographic features may represent multiple valid area codes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MEXICO_INITIAL_VIEW } from "./constants";

export const mexicoPhoneCodesMap = createMapConfig({
  id: "mexico-phone-codes",
  geojsonUrl: "/data/countries/mexico/geojson/phone-codes.geojson",
  featureProperty: "area_codes",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  promoteId: "phone_code_id",

  initialView: MEXICO_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "area_codes",
  },
});
