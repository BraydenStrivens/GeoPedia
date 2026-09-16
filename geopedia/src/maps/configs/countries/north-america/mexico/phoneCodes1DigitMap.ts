import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Mexico's eight 1-digit telephone-code regions.
 *
 * The geometry is derived by dissolving the full phone-code regions according
 * to their first digit.
 */
export const mexicoPhoneCodes1DigitMap = createMapConfig({
  id: "mexico-phone-codes-1-digit",

  geojsonUrl:
    "/data/countries/mexico/geojson/phone-code-prefixes.geojson",

  featureProperty: "prefix",

  style: {
    type: "maptiler",
  },

  promoteId: "prefix",

  initialView: {
    center: [-102, 23.5],
    zoom: 3.6,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "prefix",
  },
});
