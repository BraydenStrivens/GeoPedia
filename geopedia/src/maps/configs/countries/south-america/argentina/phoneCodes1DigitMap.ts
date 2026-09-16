/**
 * Map configuration for Argentina's first-digit geographic telephone-code
 * regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ARGENTINA_INITIAL_VIEW } from "./constants";

export const argentinaPhoneCodes1DigitMap = createMapConfig({
  id: "argentina-phone-codes-1-digit",

  geojsonUrl:
    "/data/countries/argentina/geojson/phone-codes-1-digit.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  initialView: ARGENTINA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
