/**
 * Map configuration for Brazil's 1-digit telephone area-code groups.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BRAZIL_INITIAL_VIEW } from "./constants";

export const brazilPhoneCodes1DigitMap = createMapConfig({
  id: "brazil-phone-codes-1-digit",

  geojsonUrl:
    "/data/countries/brazil/geojson/phone-codes-1-digit.geojson",

  featureProperty: "phone_code",
  promoteId: "id",

  initialView: BRAZIL_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "phone_code",
  },
});
