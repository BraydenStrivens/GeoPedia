/**
 * Map configuration for Argentina's first-level administrative divisions.
 *
 * Includes the country's 23 provinces and the Autonomous City of Buenos Aires.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ARGENTINA_INITIAL_VIEW } from "./constants";

export const argentinaProvincesMap = createMapConfig({
  id: "argentina-provinces",

  geojsonUrl: "/data/countries/argentina/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: ARGENTINA_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
