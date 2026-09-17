/**
 * Map configuration for United States geographic telephone area codes.
 *
 * Individual geographic features may represent multiple valid area codes.
 */

import { createMapConfig } from "../../../createMapConfig";
import { USA_INITIAL_VIEW } from "./constants";

export const usAreaCodesMap = createMapConfig({
  id: "us-area-codes",
  geojsonUrl: "/data/countries/usa/geojson/area-codes.geojson",

  featureProperty: "id",

  promoteId: "id",

  initialView: USA_INITIAL_VIEW,

  hover: {
    labelProperty: "id",
  },
});
