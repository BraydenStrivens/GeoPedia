/**
 * Map configuration for Taiwan's county-level divisions.
 *
 * The map contains 22 county-level features, including counties, cities,
 * and special municipalities. Features use county_id as their stable map
 * identity while county provides the player-facing label.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TAIWAN_INITIAL_VIEW } from "./constants";

export const taiwanCountiesMap = createMapConfig({
  id: "taiwan-counties",
  geojsonUrl: "/data/countries/taiwan/geojson/counties.geojson",

  featureProperty: "county",
  promoteId: "county_id",

  initialView: TAIWAN_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.25,
    },
  },

  hover: {
    labelProperty: "county",
  },
});
