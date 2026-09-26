/**
 * Map configuration for South Korea's provinces.
 *
 * Features use province_id as their stable map identity. Province names remain
 * available separately for hover labels and other player-facing UI.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_KOREA_INITIAL_VIEW } from "./constants";

export const southKoreaProvincesMap = createMapConfig({
  id: "south-korea-provinces",
  geojsonUrl: "/data/countries/south-korea/geojson/provinces.geojson",

  featureProperty: "province",
  promoteId: "province_id",

  initialView: SOUTH_KOREA_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
