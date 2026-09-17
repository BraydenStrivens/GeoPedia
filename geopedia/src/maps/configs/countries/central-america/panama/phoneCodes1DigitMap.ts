/**
 * Map configuration for Panama's geographically useful 1-digit telephone
 * prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PANAMA_INITIAL_VIEW } from "./constants";

export const panamaPhoneCodes1DigitMap = createMapConfig({
  id: "panama-phone-codes-1-digit",

  geojsonUrl:
    "/data/countries/panama/geojson/phone-codes-1-digit.geojson",

  featureProperty: "name",
  promoteId: "id",

  initialView: PANAMA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
