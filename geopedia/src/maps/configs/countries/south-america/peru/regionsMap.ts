/**
 * Map configuration for Peru's first-level administrative regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PERU_INITIAL_VIEW } from "./constants";

export const peruRegionsMap = createMapConfig({
  id: "peru-regions",
  geojsonUrl: "/data/countries/peru/geojson/regions.geojson",

  featureProperty: "region",
  promoteId: "region_id",

  initialView: PERU_INITIAL_VIEW,

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "region",
  },
});
