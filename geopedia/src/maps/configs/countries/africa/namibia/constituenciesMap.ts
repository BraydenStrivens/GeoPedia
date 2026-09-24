/**
 * Map configuration for Namibia's constituencies.
 *
 * Features use the canonical constituency_id property for map identity and
 * answers. Each feature also contains its parent region hierarchy.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { NAMIBIA_INITIAL_VIEW } from "./constants";

export const namibiaConstituenciesMap = createMapConfig({
  id: "namibia-constituencies",
  geojsonUrl:
    "/data/countries/namibia/geojson/constituencies.geojson",

  featureProperty: "constituency_id",
  promoteId: "constituency_id",

  initialView: NAMIBIA_INITIAL_VIEW,

  layers: {
    borders: {
      width: 0.75,
    },
  },

  hover: {
    labelProperty: "constituency",
  },
});
