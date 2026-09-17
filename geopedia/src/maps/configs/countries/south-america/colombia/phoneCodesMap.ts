/**
 * Map configuration for Colombia's geographic fixed-line telephone area codes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { COLOMBIA_INITIAL_VIEW } from "./constants";

export const colombiaPhoneCodesMap = createMapConfig({
  id: "colombia-phone-codes",

  geojsonUrl: "/data/countries/colombia/geojson/phone-codes.geojson",

  featureProperty: "phone_code",
  promoteId: "id",

  initialView: COLOMBIA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "phone_code",
  },
});
