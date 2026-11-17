/**
 * Map configuration for Bangladesh ADM1 (divisions).
 */
import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BANGLADESH_INITIAL_VIEW } from "./constants";

export const bangladeshDivisionsMap = createMapConfig({
  id: "bangladesh-divisions",
  geojsonUrl:
    "/data/countries/bangladesh/geojson/bangladesh_adm1.geojson",
  featureProperty: "admin_id",

  promoteId: "admin_id",

  initialView: BANGLADESH_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
