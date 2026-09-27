/**
 * Map configuration for Taiwan's detailed telephone area-code regions.
 *
 * A geographic feature may represent multiple valid telephone area codes.
 * The feature's stable `id` joins those codes with "-", while `area_codes`
 * contains the individual answers used by the feature quiz.
 *
 * The quiz configuration replaces the generic map label with the values from
 * `area_codes`, displaying multi-answer features with "/" between answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { TAIWAN_INITIAL_VIEW } from "./constants";

export const taiwanAreaCodesMap = createMapConfig({
  id: "taiwan-area-codes",
  geojsonUrl: "/data/countries/taiwan/geojson/area-codes.geojson",

  featureProperty: "id",
  promoteId: "id",

  initialView: TAIWAN_INITIAL_VIEW,

  hover: {
    labelProperty: "id",
  },
});
