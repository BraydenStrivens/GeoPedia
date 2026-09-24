/**
 * Map configuration for Namibia's geographic telephone area codes.
 *
 * Features use the canonical area_code property for map identity, answers,
 * and hover labels.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { NAMIBIA_INITIAL_VIEW } from "./constants";

export const namibiaAreaCodesMap = createMapConfig({
  id: "namibia-area-codes",
  geojsonUrl: "/data/countries/namibia/geojson/area-codes.geojson",

  featureProperty: "area_code",
  promoteId: "area_code",

  initialView: NAMIBIA_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code",
  },
});
