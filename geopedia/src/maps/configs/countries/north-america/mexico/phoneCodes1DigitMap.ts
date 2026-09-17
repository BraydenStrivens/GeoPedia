/**
 * Map configuration for Mexico's 1-digit telephone area-code groups.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { MEXICO_INITIAL_VIEW } from "./constants";

export const mexicoPhoneCodes1DigitMap = createMapConfig({
  id: "mexico-phone-codes-1-digit",
  geojsonUrl:
    "/data/countries/mexico/geojson/phone-code-prefixes.geojson",
  featureProperty: "prefix",

  promoteId: "prefix",

  initialView: MEXICO_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "prefix",
  },
});
