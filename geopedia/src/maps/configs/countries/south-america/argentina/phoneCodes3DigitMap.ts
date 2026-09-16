/**
 * Map configuration for Argentina's three-digit geographic telephone-code
 * regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ARGENTINA_INITIAL_VIEW } from "./constants";

export const argentinaPhoneCodes3DigitMap = createMapConfig({
  id: "argentina-phone-codes-3-digit",

  geojsonUrl:
    "/data/countries/argentina/geojson/phone-codes-3-digit.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: ARGENTINA_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code",
  },
});
