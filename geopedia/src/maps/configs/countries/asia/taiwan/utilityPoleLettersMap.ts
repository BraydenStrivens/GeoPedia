/**
 * Map configuration for Taiwan's utility-pole first-letter regions.
 *
 * The map contains 20 geographic grid regions used by the first letter
 * of Taiwan utility-pole plate codes. The original rectangular grid is
 * clipped to Taiwan's coastline so only relevant land areas are interactive.
 *
 * Features use utility_pole_letter as both their stable map identity and
 * player-facing label because each grid letter is unique.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TAIWAN_INITIAL_VIEW } from "./constants";

export const taiwanUtilityPoleLettersMap = createMapConfig({
  id: "taiwan-utility-pole-letters",
  geojsonUrl:
    "/data/countries/taiwan/geojson/utility-pole-letters.geojson",

  featureProperty: "utility_pole_letter",
  promoteId: "utility_pole_letter",

  initialView: TAIWAN_INITIAL_VIEW,

  hover: {
    labelProperty: "utility_pole_letter",
  },
});
