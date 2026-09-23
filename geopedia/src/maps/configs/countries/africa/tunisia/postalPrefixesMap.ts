/**
 * Map configuration for Tunisia's 2-digit postal-code prefixes.
 *
 * The map is derived from Tunisia's simplified governorate geometry.
 * Governorates with identical complete postal-prefix answer sets are merged,
 * while partially shared prefixes are handled by the quiz's multiple-answer
 * behavior.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TUNISIA_INITIAL_VIEW } from "./constants";

export const tunisiaPostalPrefixesMap = createMapConfig({
  id: "tunisia-postal-prefixes",

  geojsonUrl:
    "/data/countries/tunisia/geojson/postal-prefixes.geojson",

  featureProperty: "postal_prefix_id",
  promoteId: "postal_prefix_id",

  initialView: TUNISIA_INITIAL_VIEW,

  hover: {
    labelProperty: "governorate",
  },
});
