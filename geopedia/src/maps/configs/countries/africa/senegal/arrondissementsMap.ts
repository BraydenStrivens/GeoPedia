/**
 * Map configuration for Senegal's third-level administrative arrondissements.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { SENEGAL_INITIAL_VIEW } from "./constants";

export const senegalArrondissementsMap = createMapConfig({
  id: "senegal-arrondissements",

  geojsonUrl:
    "/data/countries/senegal/geojson/arrondissements.geojson",

  featureProperty: "arrondissement_id",
  promoteId: "arrondissement_id",

  initialView: SENEGAL_INITIAL_VIEW,

  hover: {
    labelProperty: "arrondissement",
  },
});
