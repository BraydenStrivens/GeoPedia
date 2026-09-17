/**
 * Map configuration for the U.S. Virgin Islands' islands.
 */

import { createMapConfig } from "../../../createMapConfig";
import { US_VIRGIN_ISLANDS_INITIAL_VIEW } from "./constants";

export const usVirginIslandsIslandsMap = createMapConfig({
  id: "us-virgin-islands-islands",

  geojsonUrl:
    "/data/countries/us-virgin-islands/geojson/islands.geojson",

  featureProperty: "name",
  promoteId: "island_id",

  initialView: US_VIRGIN_ISLANDS_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
