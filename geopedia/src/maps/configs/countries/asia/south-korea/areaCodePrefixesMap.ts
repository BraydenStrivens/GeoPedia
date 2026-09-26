import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_KOREA_INITIAL_VIEW } from "./constants";

export const southKoreaAreaCodePrefixesMap = createMapConfig({
  id: "south-korea-area-code-prefixes",
  geojsonUrl:
    "/data/countries/south-korea/geojson/area-code-prefixes.geojson",

  featureProperty: "area_code_prefix",
  promoteId: "area_code_prefix",

  initialView: SOUTH_KOREA_INITIAL_VIEW,

  hover: {
    labelProperty: "area_code_prefix",
  },
});
