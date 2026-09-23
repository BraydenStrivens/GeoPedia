/**
 * Map configuration for Uganda's four regions.
 *
 * Features use the canonical region_id property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { UGANDA_INITIAL_VIEW } from "./constants";

export const ugandaRegionsMap = createMapConfig({
  id: "uganda-regions",
  geojsonUrl: "/data/countries/uganda/geojson/regions.geojson",

  featureProperty: "region_id",
  promoteId: "region_id",

  initialView: UGANDA_INITIAL_VIEW,

  hover: {
    labelProperty: "region",
  },
});
