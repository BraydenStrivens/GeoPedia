/**
 * Map configuration for Ecuador's 24 provinces.
 *
 * Each feature uses the official ADM1 PCODE as its stable feature ID and
 * stores the province name in the `province` property.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ECUADOR_INITIAL_VIEW } from "./constants";

export const ecuadorProvincesMap = createMapConfig({
  id: "ecuador-provinces",

  geojsonUrl: "/data/countries/ecuador/geojson/provinces.geojson",

  featureProperty: "province",
  promoteId: "province_id",

  initialView: ECUADOR_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "province",
  },
});
