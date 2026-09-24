/**
 * Map configuration for Namibia's regions.
 *
 * Features use the canonical region_id property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { NAMIBIA_INITIAL_VIEW } from "./constants";

export const namibiaRegionsMap = createMapConfig({
  id: "namibia-regions",
  geojsonUrl: "/data/countries/namibia/geojson/regions.geojson",

  featureProperty: "region_id",
  promoteId: "region_id",

  initialView: NAMIBIA_INITIAL_VIEW,

  hover: {
    labelProperty: "region",
  },
});
