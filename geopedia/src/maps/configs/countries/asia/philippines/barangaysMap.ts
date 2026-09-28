/**
 * Map configuration for the Philippines' barangays.
 *
 * Features use the canonical barangay_id property for map identity and
 * answers. Answer labels are heavily throttled because the map contains more
 * than 42,000 subdivisions.
 *
 * The public barangay GeoJSON is intentionally being kept at relatively high
 * detail initially so its appearance and performance can be evaluated in the
 * finished quiz before deciding whether to simplify it further.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { PHILIPPINES_INITIAL_VIEW } from "./constants";

export const philippinesBarangaysMap = createMapConfig({
  id: "philippines-barangays",
  geojsonUrl: "/data/countries/philippines/geojson/barangays.geojson",

  featureProperty: "barangay_id",
  promoteId: "barangay_id",

  initialView: PHILIPPINES_INITIAL_VIEW,

  answerLabels: {
    densityThreshold: 100,
    initialMaxLabels: 25,
    labelsPerZoom: 75,
  },

  layers: {
    borders: {
      width: 0.5,
    },
  },

  hover: {
    labelProperty: "barangay",
  },
});
