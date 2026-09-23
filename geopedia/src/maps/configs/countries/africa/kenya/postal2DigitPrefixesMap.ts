/**
 * Map configuration for Kenya's 2-digit postal-code prefixes.
 *
 * Each feature represents one dissolved 2-digit postal region. The
 * postal_prefix property is both the stable map identity and quiz answer.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { KENYA_INITIAL_VIEW } from "./constants";

export const kenyaPostal2DigitPrefixesMap = createMapConfig({
  id: "kenya-postal-2-digit-prefixes",
  geojsonUrl:
    "/data/countries/kenya/geojson/2-digit-postal-prefixes.geojson",

  featureProperty: "postal_prefix",
  promoteId: "postal_prefix",

  initialView: KENYA_INITIAL_VIEW,

  hover: {
    labelProperty: "postal_prefix",
  },
});
