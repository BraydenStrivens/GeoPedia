/**
 * Map configuration for the U.S. Virgin Islands' ZIP codes.
 */

import { createMapConfig } from "../../../createMapConfig";
import { US_VIRGIN_ISLANDS_INITIAL_VIEW } from "./constants";

export const usVirginIslandsZipCodesMap = createMapConfig({
  id: "us-virgin-islands-zip-codes",

  geojsonUrl:
    "/data/countries/us-virgin-islands/geojson/zip-codes.geojson",

  featureProperty: "zip_code",
  promoteId: "zip_code",

  initialView: US_VIRGIN_ISLANDS_INITIAL_VIEW,

  hover: {
    labelProperty: "zip_code",
  },
});
