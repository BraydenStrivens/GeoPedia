/**
 * Map configuration for Taiwan's province-level divisions.
 *
 * The map contains 7 province-level features. Features use province_id
 * as their stable map identity while province provides the player-facing
 * label.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TAIWAN_INITIAL_VIEW } from "./constants";

export const taiwanProvincesMap = createMapConfig({
  id: "taiwan-provinces",
  geojsonUrl: "/data/countries/taiwan/geojson/provinces.geojson",

  featureProperty: "province",
  promoteId: "province_id",

  initialView: TAIWAN_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
