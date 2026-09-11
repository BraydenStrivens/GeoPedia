import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Brazil's two-digit geographic telephone-code regions.
 */
export const brazilPhoneCodes2DigitMap = createMapConfig({
  id: "brazil-phone-codes-2-digit",

  geojsonUrl:
    "/data/countries/brazil/geojson/phone-codes-2-digit.geojson",

  featureProperty: "phone_code",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-52.5, -14.5],
    zoom: 3.2,
  },

  hover: {
    labelProperty: "phone_code",
  },
});
