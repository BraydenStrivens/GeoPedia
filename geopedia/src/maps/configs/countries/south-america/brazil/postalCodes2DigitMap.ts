/**
 * Map configuration for Brazil's 2-digit CEP postal-code regions.
 *
 * Individual geographic features may represent multiple valid CEP-2 prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BRAZIL_INITIAL_VIEW } from "./constants";

export const brazilPostalCodes2DigitMap = createMapConfig({
  id: "brazil-postal-codes",

  geojsonUrl: "/data/countries/brazil/geojson/postal-codes.geojson",

  featureProperty: "postal_codes",
  promoteId: "postal_code_id",

  initialView: BRAZIL_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "postal_codes",
  },
});
