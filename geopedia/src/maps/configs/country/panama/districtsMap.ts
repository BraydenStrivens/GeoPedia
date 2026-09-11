import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Panama's district-level administrative boundaries.
 *
 * The processed GeoJSON contains 82 structural features, including Kuna
 * Yala's `1000` hierarchy placeholder. Quiz configuration determines which
 * of those features are included as questions.
 */
export const panamaDistrictsMap = createMapConfig({
  id: "panama-districts",

  geojsonUrl: "/data/countries/panama/geojson/districts.geojson",

  featureProperty: "name",
  promoteId: "id",

  style: {
    type: "maptiler",
  },

  initialView: {
    center: [-80.5, 8.5],
    zoom: 5.7,
  },

  hover: {
    labelProperty: "name",
  },
});
