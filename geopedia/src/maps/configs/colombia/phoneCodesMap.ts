import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Colombia's geographic fixed-line telephone-code
 * regions.
 */
export const colombiaPhoneCodesMap = createMapConfig({
  id: "colombia-phone-codes",

  geojsonUrl: "/data/countries/colombia/geojson/phone-codes.geojson",

  featureProperty: "phone_code",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-74.3, 4.5],
    zoom: 4.6,
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
