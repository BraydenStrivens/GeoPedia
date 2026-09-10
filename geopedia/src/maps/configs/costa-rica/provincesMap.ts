import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Costa Rica's 7 provinces.
 *
 * Province IDs correspond to the first digit of Costa Rica's administrative
 * codes and can also be used as 1-digit postal-code prefixes.
 */
export const costaRicaProvincesMap = createMapConfig({
  id: "costa-rica-provinces",
  geojsonUrl: "/data/countries/costa-rica/geojson/provinces.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "province_id",

  initialView: {
    center: [-84.1, 9.8],
    zoom: 6.5,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
