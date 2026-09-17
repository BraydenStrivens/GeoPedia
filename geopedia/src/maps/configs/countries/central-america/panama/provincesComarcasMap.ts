/**
 * Map configuration for Panama's 10 provinces and four province-level
 * comarcas.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PANAMA_INITIAL_VIEW } from "./constants";

export const panamaProvincesComarcasMap = createMapConfig({
  id: "panama-provinces-comarcas",

  geojsonUrl:
    "/data/countries/panama/geojson/provinces-comarcas.geojson",

  featureProperty: "name",
  promoteId: "id",

  initialView: PANAMA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
