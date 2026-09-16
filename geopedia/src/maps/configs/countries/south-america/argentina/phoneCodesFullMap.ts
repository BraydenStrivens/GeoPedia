/**
 * Map configuration for Argentina's complete geographic telephone area codes.
 *
 * The features contain the actual 2-, 3-, and 4-digit area codes rather than
 * prefixes truncated to a common length.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ARGENTINA_INITIAL_VIEW } from "./constants";

export const argentinaPhoneCodesFullMap = createMapConfig({
  id: "argentina-phone-codes-full",

  geojsonUrl:
    "/data/countries/argentina/geojson/phone-codes-full.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: ARGENTINA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
