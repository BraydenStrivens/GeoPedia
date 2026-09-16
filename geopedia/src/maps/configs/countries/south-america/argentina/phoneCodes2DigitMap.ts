/**
 * Map configuration for Argentina's two-digit geographic telephone-code
 * regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ARGENTINA_INITIAL_VIEW } from "./constants";

export const argentinaPhoneCodes2DigitMap = createMapConfig({
  id: "argentina-phone-codes-2-digit",

  geojsonUrl:
    "/data/countries/argentina/geojson/phone-codes-2-digit.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  initialView: ARGENTINA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.25,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
