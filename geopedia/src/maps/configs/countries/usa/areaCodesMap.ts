/**
 * Defines the shared map configuration for United States telephone
 * area-code geography.
 *
 * The processed GeoJSON contains one geographic feature for each unique
 * area-code region. Overlay area codes that share identical boundaries
 * are stored together within the feature's `area_codes` property.
 */

import { createMapConfig } from "../../createMapConfig";

export const usAreaCodesMap = createMapConfig({
  id: "us-area-codes",
  geojsonUrl: "/data/countries/usa/geojson/area-codes.geojson",

  featureProperty: "id",

  style: {
    type: "maptiler",
  },

  /*
   * Each processed feature contains a stable generated ID such as
   * "201-551" or "214-469-945-972".
   */
  promoteId: "id",

  initialView: {
    center: [-98.5, 39.8],
    zoom: 3.5,
  },

  hover: {
    labelProperty: "id",
  },
});
