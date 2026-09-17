/**
 * Map configuration for Puerto Rico's ZIP codes.
 */

import { createMapConfig } from "../../../createMapConfig";
import { PUERTO_RICO_INITIAL_VIEW } from "./constants";

export const puertoRicoZipCodesMap = createMapConfig({
  id: "puerto-rico-zip-codes",

  geojsonUrl: "/data/countries/puerto-rico/geojson/zip-codes.geojson",

  featureProperty: "zip_code",
  promoteId: "zip_code",

  initialView: PUERTO_RICO_INITIAL_VIEW,

  hover: {
    labelProperty: "zip_code",
  },
});
