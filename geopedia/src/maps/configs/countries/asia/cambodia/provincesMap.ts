/**
 * Map configuration for Cambodia's first-level administrative divisions.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { CAMBODIA_INITIAL_VIEW } from "./constants";

export const cambodiaProvincesMap = createMapConfig({
  id: "cambodia-provinces",
  geojsonUrl: "/data/countries/cambodia/geojson/provinces.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: CAMBODIA_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
