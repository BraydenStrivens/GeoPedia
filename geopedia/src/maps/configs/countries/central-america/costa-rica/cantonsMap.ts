/**
 * Map configuration for Costa Rica's 84 cantons.
 *
 * Canton IDs correspond to Costa Rica's 3-digit administrative codes and can
 * also be used as 3-digit postal-code prefixes.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { COSTA_RICA_INITIAL_VIEW } from "./constants";

export const costaRicaCantonsMap = createMapConfig({
  id: "costa-rica-cantons",
  geojsonUrl: "/data/countries/costa-rica/geojson/cantons.geojson",
  featureProperty: "name",

  promoteId: "canton_id",

  initialView: COSTA_RICA_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
