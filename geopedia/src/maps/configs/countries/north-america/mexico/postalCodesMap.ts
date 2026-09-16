import { createMapConfig } from "@/maps/configs/createMapConfig";
import type { MapConfig } from "@/maps/types";

/**
 * Configures the map used by Mexico's 2-digit postal-code prefix quiz.
 *
 * Each feature represents one literal 2-digit prefix derived from SEPOMEX
 * postal-code geometry.
 */
export const mexicoPostalCodesMap: MapConfig = createMapConfig({
  id: "mexico-postal-codes",

  geojsonUrl:
    "/data/countries/mexico/geojson/postal-code-prefixes.geojson",

  featureProperty: "postal_code_prefix",

  promoteId: "postal_code_prefix_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-102.5, 23.6],
    zoom: 4.2,
  },

  hover: {
    labelProperty: "postal_code_prefix",
  },
});
