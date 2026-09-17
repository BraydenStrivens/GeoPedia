/**
 * Map configuration for Brazil's five geographic regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BRAZIL_INITIAL_VIEW } from "./constants";

export const brazilRegionsMap = createMapConfig({
  id: "brazil-regions",

  geojsonUrl: "/data/countries/brazil/geojson/regions.geojson",

  featureProperty: "name",
  promoteId: "id",

  initialView: BRAZIL_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
