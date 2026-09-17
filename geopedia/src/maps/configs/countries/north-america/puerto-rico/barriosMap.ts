/**
 * Map configuration for Puerto Rico's barrios.
 */

import { createMapConfig } from "../../../createMapConfig";
import { PUERTO_RICO_INITIAL_VIEW } from "./constants";

export const puertoRicoBarriosMap = createMapConfig({
  id: "puerto-rico-barrios",

  geojsonUrl: "/data/countries/puerto-rico/geojson/barrios.geojson",

  featureProperty: "name",
  promoteId: "barrio_id",

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 75,
    labelsPerZoom: 100,
  },

  initialView: PUERTO_RICO_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
