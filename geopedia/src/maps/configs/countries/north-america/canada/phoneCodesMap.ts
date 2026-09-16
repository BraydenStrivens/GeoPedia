import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Canada's legacy telephone area-code regions.
 *
 * The underlying GeoJSON contains 19 geographically distinct legacy area-code
 * regions used by the Canada Phone Codes quiz. Modern overlay codes are not
 * represented because they share geography with the older codes and therefore
 * do not provide additional geographic regions to identify.
 *
 * Each GeoJSON feature uses its three-digit `area_code` as both its stable
 * feature identifier and its primary display property.
 *
 * Province and territory membership is stored separately in each feature's
 * `provinces` property for quiz grouping and is not needed by the map itself.
 */
export const canadaPhoneCodesMap = createMapConfig({
  id: "canada-phone-codes",
  geojsonUrl: "/data/countries/canada/geojson/phone-codes.geojson",
  featureProperty: "area_code",

  style: {
    type: "maptiler",
  },

  promoteId: "area_code",

  initialView: {
    center: [-96, 61],
    zoom: 2.4,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "area_code",
  },
});
