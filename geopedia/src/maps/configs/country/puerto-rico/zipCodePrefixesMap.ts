import { createMapConfig } from "../../createMapConfig";

/**
 * Map configuration for Puerto Rico's 3-digit ZIP-code prefixes.
 */
export const puertoRicoZipCodePrefixesMap = createMapConfig({
  id: "puerto-rico-zip-code-prefixes",

  geojsonUrl:
    "/data/countries/puerto-rico/geojson/zip-code-prefixes.geojson",

  featureProperty: "prefix_3",
  promoteId: "prefix_3",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-66.45, 18.22],
    zoom: 8,
  },

  hover: {
    labelProperty: "prefix_3",
  },
});
