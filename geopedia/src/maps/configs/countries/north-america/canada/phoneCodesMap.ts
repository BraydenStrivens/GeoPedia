/**
 * Map configuration for Canada's geographic telephone area codes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CANADA_INITIAL_VIEW } from "./constants";

export const canadaPhoneCodesMap = createMapConfig({
  id: "canada-phone-codes",
  geojsonUrl: "/data/countries/canada/geojson/phone-codes.geojson",
  featureProperty: "area_code",

  promoteId: "area_code",

  initialView: CANADA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
