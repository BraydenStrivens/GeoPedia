/**
 * Map configuration for Kenya's 3-digit postal-code prefixes.
 *
 * Features use postal_region_id as their stable scalar map identity. The
 * corresponding quiz uses the postal_prefixes array for accepted answers,
 * allowing multiple prefixes to share the same postal-region geometry.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { KENYA_INITIAL_VIEW } from "./constants";

export const kenyaPostal3DigitPrefixesMap = createMapConfig({
  id: "kenya-postal-3-digit-prefixes",
  geojsonUrl:
    "/data/countries/kenya/geojson/3-digit-postal-prefixes.geojson",

  featureProperty: "postal_region_id",
  promoteId: "postal_region_id",

  initialView: KENYA_INITIAL_VIEW,

  hover: {
    labelProperty: "postal_region_id",
  },
});
