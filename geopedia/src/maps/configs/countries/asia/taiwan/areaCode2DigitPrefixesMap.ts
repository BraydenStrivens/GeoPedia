/**
 * Map configuration for Taiwan's 2-digit telephone area-code prefixes.
 *
 * Prefix features are dissolved by their complete answer sets. A feature may
 * therefore contain multiple valid prefixes in its `area_codes` array.
 *
 * The stable `id` joins all answers with "-", while the quiz configuration
 * uses `area_codes` to provide the player-facing map labels.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TAIWAN_INITIAL_VIEW } from "./constants";

export const taiwanAreaCode2DigitPrefixesMap = createMapConfig({
  id: "taiwan-area-code-prefix-2",
  geojsonUrl:
    "/data/countries/taiwan/geojson/area-code-prefix-2.geojson",

  featureProperty: "id",
  promoteId: "id",

  initialView: TAIWAN_INITIAL_VIEW,

  hover: {
    labelProperty: "id",
  },
});
