import { createMapConfig } from "../../createMapConfig";

/**
 * Map configuration for Puerto Rico's ZIP codes.
 */
export const puertoRicoZipCodesMap = createMapConfig({
  id: "puerto-rico-zip-codes",

  geojsonUrl: "/data/countries/puerto-rico/geojson/zip-codes.geojson",

  featureProperty: "zip_code",
  promoteId: "zip_code",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-66.45, 18.22],
    zoom: 8,
  },

  hover: {
    labelProperty: "zip_code",
  },
});
