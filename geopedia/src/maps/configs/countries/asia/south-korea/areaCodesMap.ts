import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SOUTH_KOREA_INITIAL_VIEW } from "./constants";

export const southKoreaAreaCodesMap = createMapConfig({
  id: "south-korea-area-codes",
  geojsonUrl:
    "/data/countries/south-korea/geojson/area-codes.geojson",

  featureProperty: "province",
  promoteId: "province_id",

  initialView: SOUTH_KOREA_INITIAL_VIEW,

  hover: {
    labelProperty: "province",
  },
});
