/**
 * Map configuration for Costa Rica's 7 provinces.
 *
 * Province IDs correspond to the first digit of Costa Rica's administrative
 * codes and can also be used as 1-digit postal-code prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { COSTA_RICA_INITIAL_VIEW } from "./constants";

export const costaRicaProvincesMap = createMapConfig({
  id: "costa-rica-provinces",
  geojsonUrl: "/data/countries/costa-rica/geojson/provinces.geojson",
  featureProperty: "name",

  promoteId: "province_id",

  initialView: COSTA_RICA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
