import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Panama's geographically useful 1-digit telephone
 * prefixes.
 */
export const panamaPhoneCodes1DigitMap = createMapConfig({
  id: "panama-phone-codes-1-digit",

  geojsonUrl:
    "/data/countries/panama/geojson/phone-codes-1-digit.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-80.5, 8.5],
    zoom: 5.7,
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
