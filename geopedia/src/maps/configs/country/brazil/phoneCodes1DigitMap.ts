import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Brazil's first-digit telephone-code regions.
 */
export const brazilPhoneCodes1DigitMap = createMapConfig({
  id: "brazil-phone-codes-1-digit",

  geojsonUrl:
    "/data/countries/brazil/geojson/phone-codes-1-digit.geojson",

  featureProperty: "phone_code",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-52.5, -14.5],
    zoom: 3.2,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "phone_code",
  },
});
