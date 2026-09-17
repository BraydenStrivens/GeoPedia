/**
 * Map configuration for Brazil's 2-digit telephone area codes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BRAZIL_INITIAL_VIEW } from "./constants";

export const brazilPhoneCodes2DigitMap = createMapConfig({
  id: "brazil-phone-codes-2-digit",

  geojsonUrl:
    "/data/countries/brazil/geojson/phone-codes-2-digit.geojson",

  featureProperty: "phone_code",
  promoteId: "id",

  initialView: BRAZIL_INITIAL_VIEW,

  hover: {
    labelProperty: "phone_code",
  },
});
