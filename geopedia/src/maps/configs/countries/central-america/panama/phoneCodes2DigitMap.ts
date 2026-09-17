/**
 * Map configuration for Panama's more precise regional telephone prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PANAMA_INITIAL_VIEW } from "./constants";

export const panamaPhoneCodes2DigitMap = createMapConfig({
  id: "panama-phone-codes-2-digit",

  geojsonUrl:
    "/data/countries/panama/geojson/phone-codes-2-digit.geojson",

  featureProperty: "name",
  promoteId: "id",

  initialView: PANAMA_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
