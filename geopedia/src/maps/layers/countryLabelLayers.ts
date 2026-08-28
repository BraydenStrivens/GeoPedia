import type * as maplibregl from "maplibre-gl";

/**
 * GeoJSON source containing GeoPedia's generated country-label anchor points.
 */
const COUNTRY_LABEL_SOURCE_ID = "geopedia-country-labels";

/**
 * Symbol layer used for GeoPedia-owned country names.
 */
export const COUNTRY_LABEL_LAYER_ID = "geopedia-country-labels";

/**
 * Runtime URL of the generated country-label dataset.
 */
const COUNTRY_LABEL_GEOJSON_URL =
  "/data/geojson/world/country-labels.geojson";

/**
 * Updates which country labels are eligible at the supplied zoom level.
 *
 * Country labels are completely excluded until the map reaches their
 * individually calculated minimum zoom.
 *
 * `to-number` also protects against malformed or missing GeoJSON values.
 * A missing value falls back to 999, keeping that feature hidden rather
 * than accidentally allowing it to appear.
 *
 * @param map - MapLibre map containing the country-label layer.
 * @param zoom - Current map zoom.
 */
export function updateCountryLabelFilter(
  map: maplibregl.Map,
  zoom: number,
): void {
  if (!map.getLayer(COUNTRY_LABEL_LAYER_ID)) {
    return;
  }

  map.setFilter(COUNTRY_LABEL_LAYER_ID, [
    "all",

    // The country has become visible.
    ["<=", ["to-number", ["get", "countryLabelMinZoom"], 999], zoom],

    // The map has not zoomed beyond this country's contextual range.
    [">", ["to-number", ["get", "countryLabelMaxZoom"], -999], zoom],
  ]);
}

/**
 * Adds GeoPedia's contextual country-label source and symbol layer.
 *
 * Each country feature already contains its calculated minimum label zoom.
 * The layer therefore uses a feature expression for opacity so individual
 * countries become visible according to geographic size.
 *
 * Country labels intentionally use GeoPedia's own anchor points and priority
 * metadata rather than MapTiler's country symbol layers. This allows country
 * names and settlement labels to participate in one controlled labeling
 * system.
 *
 * @param map - Initialized MapLibre map whose style has finished loading.
 */
export function addCountryLabelLayers(map: maplibregl.Map): void {
  if (map.getSource(COUNTRY_LABEL_SOURCE_ID)) {
    return;
  }

  map.addSource(COUNTRY_LABEL_SOURCE_ID, {
    type: "geojson",
    data: COUNTRY_LABEL_GEOJSON_URL,
  });

  map.addLayer({
    id: COUNTRY_LABEL_LAYER_ID,

    type: "symbol",

    source: COUNTRY_LABEL_SOURCE_ID,

    minzoom: 1.5,

    layout: {
      "text-field": ["get", "name"],

      "text-font": ["Noto Sans Bold"],

      "text-size": [
        "interpolate",
        ["linear"],
        ["zoom"],

        1.5,
        14,

        4,
        16,

        7,
        18,

        10,
        20,
      ],

      "text-letter-spacing": 0.08,

      "text-max-width": 10,

      "text-allow-overlap": false,

      "text-ignore-placement": false,

      "text-optional": false,

      visibility: "visible",
    },

    paint: {
      "text-color": "#4b5563",
      "text-halo-color": "rgba(255, 255, 255, 0.9)",
      "text-halo-width": 1.25,
      "text-halo-blur": 0.5,
    },
  });
}
