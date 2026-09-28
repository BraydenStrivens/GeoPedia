/**
 * Map configuration for the Philippines' telephone area codes.
 *
 * Features use the domestic area_code property for map identity and answers.
 * Area-code boundaries are derived from administrative boundaries, including
 * the Bacoor City and City of San Pedro exceptions to the normal
 * province-based assignments.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PHILIPPINES_INITIAL_VIEW } from "./constants";

export const philippinesAreaCodesMap = createMapConfig({
  id: "philippines-area-codes",
  geojsonUrl:
    "/data/countries/philippines/geojson/area-codes.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  initialView: PHILIPPINES_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code",
  },
});
