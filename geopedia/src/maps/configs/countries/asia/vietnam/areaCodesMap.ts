/**
 * Map configuration for Vietnam's telephone area codes.
 *
 * The geometry follows the province boundaries used by Vietnam's area-code
 * regions and includes the two-digit prefix used for quiz grouping.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { VIETNAM_INITIAL_VIEW } from "./constants";

export const vietnamAreaCodesMap = createMapConfig({
  id: "vietnam-area-codes",
  geojsonUrl: "/data/countries/vietnam/geojson/area-codes.geojson",

  featureProperty: "province_id",
  promoteId: "province_id",

  initialView: VIETNAM_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
