/**
 * Map configuration for Tunisia's mutamadiyat (delegations).
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TUNISIA_INITIAL_VIEW } from "./constants";

export const tunisiaDelegationsMap = createMapConfig({
  id: "tunisia-delegations",

  geojsonUrl: "/data/countries/tunisia/geojson/delegations.geojson",

  featureProperty: "delegation_id",
  promoteId: "delegation_id",

  initialView: TUNISIA_INITIAL_VIEW,

  hover: {
    labelProperty: "delegation",
  },
});
