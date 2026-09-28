/**
 * Map configuration for the Philippines' 17 regions.
 *
 * Features use the canonical region_id property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PHILIPPINES_INITIAL_VIEW } from "./constants";

export const philippinesRegionsMap = createMapConfig({
  id: "philippines-regions",
  geojsonUrl: "/data/countries/philippines/geojson/regions.geojson",

  featureProperty: "region_id",
  promoteId: "region_id",

  initialView: PHILIPPINES_INITIAL_VIEW,

  hover: {
    labelProperty: "region",
  },
});
