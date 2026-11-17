/**
 * Map configuration for Bangladesh ADM2 (districts).
 * */
import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BANGLADESH_INITIAL_VIEW } from "./constants";

export const bangladeshDistrictsMap = createMapConfig({
  id: "bangladesh-districts",
  geojsonUrl:
    "/data/countries/bangladesh/geojson/bangladesh_adm2.geojson",
  featureProperty: "admin_id",

  promoteId: "admin_id",

  initialView: BANGLADESH_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
