import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Costa Rica's 84 cantons.
 *
 * Canton IDs correspond to Costa Rica's 3-digit administrative codes and can
 * also be used as 3-digit postal-code prefixes.
 */
export const costaRicaCantonsMap = createMapConfig({
  id: "costa-rica-cantons",
  geojsonUrl: "/data/countries/costa-rica/geojson/cantons.geojson",
  featureProperty: "name",

  promoteId: "canton_id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-84.1, 9.8],
    zoom: 6.5,
  },

  hover: {
    labelProperty: "name",
  },
});
