import { createMapConfig } from "../../createMapConfig";

/**
 * Map configuration for the U.S. Virgin Islands' ZIP codes.
 */
export const usVirginIslandsZipCodesMap = createMapConfig({
  id: "us-virgin-islands-zip-codes",

  geojsonUrl:
    "/data/countries/us-virgin-islands/geojson/zip-codes.geojson",

  featureProperty: "zip_code",
  promoteId: "zip_code",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-64.78, 18.05],
    zoom: 8,
  },

  hover: {
    labelProperty: "zip_code",
  },
});
