import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Panama's more precise regional telephone prefixes.
 */
export const panamaPhoneCodes2DigitMap = createMapConfig({
  id: "panama-phone-codes-2-digit",

  geojsonUrl:
    "/data/countries/panama/geojson/phone-codes-2-digit.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-80.5, 8.5],
    zoom: 5.7,
  },

  hover: {
    labelProperty: "name",
  },
});
