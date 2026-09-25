/**
 * Map configuration for Eswatini's tinkhundla.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { ESWATINI_INITIAL_VIEW } from "./constants";

export const eswatiniTinkhundlaMap = createMapConfig({
  id: "eswatini-tinkhundla",
  geojsonUrl: "/data/countries/eswatini/geojson/tinkhundla.geojson",

  featureProperty: "inkhundla",
  promoteId: "inkhundla_id",

  initialView: ESWATINI_INITIAL_VIEW,

  hover: {
    labelProperty: "inkhundla",
  },
});
