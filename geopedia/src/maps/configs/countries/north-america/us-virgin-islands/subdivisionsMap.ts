/**
 * Map configuration for the U.S. Virgin Islands' subdivisions.
 */

import { createMapConfig } from "../../../createMapConfig";
import { US_VIRGIN_ISLANDS_INITIAL_VIEW } from "./constants";

export const usVirginIslandsSubdivisionsMap = createMapConfig({
  id: "us-virgin-islands-subdivisions",

  geojsonUrl:
    "/data/countries/us-virgin-islands/geojson/subdivisions.geojson",

  featureProperty: "name",
  promoteId: "subdivision_id",

  initialView: US_VIRGIN_ISLANDS_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
