/**
 * Map configuration for Mexico's postal-code regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";
import type { MapConfig } from "@/maps/types";

import { MEXICO_INITIAL_VIEW } from "./constants";

export const mexicoPostalCodesMap: MapConfig = createMapConfig({
  id: "mexico-postal-codes",
  geojsonUrl:
    "/data/countries/mexico/geojson/postal-code-prefixes.geojson",
  featureProperty: "postal_code_prefix",

  promoteId: "postal_code_prefix_id",

  initialView: MEXICO_INITIAL_VIEW,

  hover: {
    labelProperty: "postal_code_prefix",
  },
});
