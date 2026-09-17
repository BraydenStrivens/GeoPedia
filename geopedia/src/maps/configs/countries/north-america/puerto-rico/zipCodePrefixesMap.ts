/**
 * Map configuration for Puerto Rico's 3-digit ZIP-code prefixes.
 */

import { createMapConfig } from "../../../createMapConfig";
import { PUERTO_RICO_INITIAL_VIEW } from "./constants";

export const puertoRicoZipCodePrefixesMap = createMapConfig({
  id: "puerto-rico-zip-code-prefixes",

  geojsonUrl:
    "/data/countries/puerto-rico/geojson/zip-code-prefixes.geojson",

  featureProperty: "prefix_3",
  promoteId: "prefix_3",

  initialView: PUERTO_RICO_INITIAL_VIEW,

  hover: {
    labelProperty: "prefix_3",
  },
});
