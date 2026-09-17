import { createMapConfig } from "../../../createMapConfig";
import { PUERTO_RICO_INITIAL_VIEW } from "./constants";

/**
 * Map configuration for Puerto Rico's municipalities.
 */
export const puertoRicoMunicipalitiesMap = createMapConfig({
  id: "puerto-rico-municipalities",

  geojsonUrl:
    "/data/countries/puerto-rico/geojson/municipalities.geojson",

  featureProperty: "name",
  promoteId: "municipality_id",

  initialView: PUERTO_RICO_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
