import { createMapConfig } from "@/maps/configs/createMapConfig";

/**
 * Map configuration for Guatemala's 22 departments.
 *
 * The underlying GeoJSON is processed from the HDX Guatemala administrative
 * boundaries dataset.
 *
 * Each feature uses the source department p-code, normalized to a two-digit
 * identifier, as its stable feature ID and stores the user-facing department
 * name in the `name` property.
 */
export const guatemalaDepartmentsMap = createMapConfig({
  id: "guatemala-departments",
  geojsonUrl: "/data/countries/guatemala/geojson/departments.geojson",
  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "department_id",

  initialView: {
    center: [-90.25, 15.7],
    zoom: 5.5,
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
