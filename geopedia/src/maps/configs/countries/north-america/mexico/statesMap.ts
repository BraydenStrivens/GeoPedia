import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Mexico's 32 federal entities.
 *
 * The underlying GeoJSON is processed from INEGI's 2025 integrated
 * geostatistical framework and contains Mexico's 31 states plus
 * Ciudad de México.
 *
 * Each feature uses INEGI's two-digit state/entity identifier as its stable
 * feature ID and stores the user-facing state name in the `name` property.
 */
export const mexicoStatesMap = createMapConfig({
  id: "mexico-states",
  geojsonUrl: "/data/countries/mexico/geojson/states.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "state_id",

  initialView: {
    center: [-102, 23.5],
    zoom: 3.6,
  },

  layers: {
    borders: {
      width: 1.5,
    },
  },

  hover: {
    labelProperty: "name",
  },
});
