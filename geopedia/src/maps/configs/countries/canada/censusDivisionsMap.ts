import { createMapConfig } from "../../createMapConfig";

/**
 * Map configuration for Canada's census divisions.
 *
 * Uses the processed Statistics Canada census division GeoJSON containing
 * all 293 census divisions across Canada's provinces and territories.
 *
 * Each feature is identified by its Census Division Unique Identifier
 * (`cduid`), while the census division's `name` property is used for
 * map interactions and hover labels.
 *
 * The initial camera matches the Canada provinces map so the full country
 * is visible when the quiz begins.
 */
export const canadaCensusDivisionsMap = createMapConfig({
  id: "canada-census-divisions",

  geojsonUrl:
    "/data/countries/canada/geojson/census-divisions.geojson",

  featureProperty: "name",

  style: {
    type: "maptiler",
  },

  promoteId: "cduid",

  answerLabels: {
    densityThreshold: 500,
    initialMaxLabels: 100,
    labelsPerZoom: 250,
  },

  initialView: {
    center: [-96, 61],
    zoom: 2.4,
  },

  hover: {
    labelProperty: "name",
  },
});
