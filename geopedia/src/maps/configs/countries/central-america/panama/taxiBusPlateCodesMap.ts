/**
 * Map configuration for Panama's regional taxi and bus licence-plate codes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PANAMA_INITIAL_VIEW } from "./constants";

export const panamaTaxiBusPlateCodesMap = createMapConfig({
  id: "panama-taxi-bus-plate-codes",

  geojsonUrl:
    "/data/countries/panama/geojson/taxi-bus-plate-codes.geojson",

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
