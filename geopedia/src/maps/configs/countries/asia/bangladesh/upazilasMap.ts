/**
 * Map configuration for Bangladesh ADM3 (upazilas).
 */
import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BANGLADESH_INITIAL_VIEW } from "./constants";

export const bangladeshUpazilasMap = createMapConfig({
  id: "bangladesh-upazilas",
  geojsonUrl:
    "/data/countries/bangladesh/geojson/bangladesh_adm3.geojson",
  featureProperty: "admin_id",

  promoteId: "admin_id",

  initialView: BANGLADESH_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 125,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  hover: {
    labelProperty: "name",
  },
});
