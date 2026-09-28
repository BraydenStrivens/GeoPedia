/**
 * Map configuration for Indonesia's seven major geographic regions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { INDONESIA_INITIAL_VIEW } from "./constants";

export const indonesiaRegionsMap = createMapConfig({
  id: "indonesia-regions",

  geojsonUrl: "/data/countries/indonesia/geojson/regions.geojson",

  featureProperty: "region_id",
  promoteId: "region_id",

  initialView: INDONESIA_INITIAL_VIEW,

  hover: {
    labelProperty: "region",
  },
});
