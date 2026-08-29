/**
 * Provides utilities for controlling layers supplied by the external base-map
 * style.
 *
 * GeoPedia separates contextual base-map content into:
 *
 * - Country labels.
 * - State/province/subdivision labels.
 * - Settlement labels.
 * - Country borders.
 * - Administrative subdivision borders.
 *
 * GeoPedia's own quiz-feature layers are controlled separately.
 */

import type * as maplibregl from "maplibre-gl";

import type { BaseMapLayerVisibilityConfig } from "@/maps/types";

/**
 * MapTiler symbol layers used for country names.
 */
const COUNTRY_LABEL_LAYER_IDS = new Set(["Country labels"]);

/**
 * MapTiler symbol layers used for first-level administrative subdivision names.
 */
const SUBDIVISION_LABEL_LAYER_IDS = new Set(["State labels"]);

/**
 * MapTiler symbol layers used for settlements and other local places.
 *
 * `Place labels` contains smaller settlements such as villages, hamlets,
 * suburbs, neighbourhoods, and similar contextual place names.
 */
const TOWN_LABEL_LAYER_IDS = new Set([
  "Capital city labels",
  "City labels",
  "Town labels",
  "Place labels",
]);

/**
 * Applies a map configuration's base-layer visibility together with the
 * current global Show Labels / Show Borders settings.
 *
 * A map configuration determines whether a category is allowed to appear.
 * The global settings act as master switches over those allowed categories.
 *
 * @param map - MapLibre map whose base-style layers should be updated.
 * @param config - Map-specific base-layer visibility configuration.
 * @param shouldShowLabels - Global master visibility for base-map labels.
 * @param shouldShowBorders - Global master visibility for base-map borders.
 */
export function applyBaseMapLayerVisibility(
  map: maplibregl.Map,
  config: BaseMapLayerVisibilityConfig | undefined,
  shouldShowLabels: boolean,
  shouldShowBorders: boolean,
): void {
  setBaseMapCountryLabelsVisible(
    map,
    shouldShowLabels && (config?.countryLabels ?? true),
  );

  setBaseMapSubdivisionLabelsVisible(
    map,
    shouldShowLabels && (config?.subdivisionLabels ?? true),
  );

  setBaseMapTownLabelsVisible(
    map,
    shouldShowLabels && (config?.townLabels ?? true),
  );

  setBaseMapCountryBordersVisible(
    map,
    shouldShowBorders && (config?.countryBorders ?? true),
  );

  setBaseMapSubdivisionBordersVisible(
    map,
    shouldShowBorders && (config?.subdivisionBorders ?? true),
  );
}

/**
 * Shows or hides MapTiler country-name labels.
 */
export function setBaseMapCountryLabelsVisible(
  map: maplibregl.Map,
  shouldShow: boolean,
): void {
  setNamedLayersVisible(map, COUNTRY_LABEL_LAYER_IDS, shouldShow);
}

/**
 * Shows or hides MapTiler state/province/subdivision labels.
 */
export function setBaseMapSubdivisionLabelsVisible(
  map: maplibregl.Map,
  shouldShow: boolean,
): void {
  setNamedLayersVisible(map, SUBDIVISION_LABEL_LAYER_IDS, shouldShow);
}

/**
 * Shows or hides MapTiler settlement labels.
 */
export function setBaseMapTownLabelsVisible(
  map: maplibregl.Map,
  shouldShow: boolean,
): void {
  setNamedLayersVisible(map, TOWN_LABEL_LAYER_IDS, shouldShow);
}

/**
 * Shows or hides country boundaries supplied by the base-map style.
 */
export function setBaseMapCountryBordersVisible(
  map: maplibregl.Map,
  shouldShow: boolean,
): void {
  for (const layer of getAdministrativeBoundaryLayers(map)) {
    if (!isCountryBoundaryLayer(layer)) {
      continue;
    }

    setLayerVisible(map, layer.id, shouldShow);
  }
}

/**
 * Shows or hides internal administrative subdivision boundaries supplied by
 * the base-map style.
 */
export function setBaseMapSubdivisionBordersVisible(
  map: maplibregl.Map,
  shouldShow: boolean,
): void {
  for (const layer of getAdministrativeBoundaryLayers(map)) {
    if (isCountryBoundaryLayer(layer)) {
      continue;
    }

    setLayerVisible(map, layer.id, shouldShow);
  }
}

/**
 * Shows or hides every base-map symbol layer.
 *
 * This helper is retained for callers that intentionally want a complete
 * base-map label master switch rather than category-specific control.
 */
export function setBaseMapLabelsVisible(
  map: maplibregl.Map,
  shouldShowLabels: boolean,
): void {
  const styleLayers = map.getStyle().layers ?? [];

  for (const layer of styleLayers) {
    if (layer.type !== "symbol") {
      continue;
    }

    setLayerVisible(map, layer.id, shouldShowLabels);
  }
}

/**
 * Shows or hides every administrative boundary supplied by the base map.
 *
 * This helper is retained as a general master switch. Category-specific code
 * should prefer the country/subdivision helpers above.
 */
export function setBaseMapBordersVisible(
  map: maplibregl.Map,
  shouldShowBorders: boolean,
): void {
  for (const layer of getAdministrativeBoundaryLayers(map)) {
    setLayerVisible(map, layer.id, shouldShowBorders);
  }
}

/**
 * Returns base-style line layers representing administrative boundaries.
 */
function getAdministrativeBoundaryLayers(
  map: maplibregl.Map,
): maplibregl.LayerSpecification[] {
  const styleLayers = map.getStyle().layers ?? [];

  return styleLayers.filter((layer) => {
    if (layer.type !== "line") {
      return false;
    }

    const sourceLayerName = getSourceLayerName(layer);
    const normalizedLayerId = layer.id.toLowerCase();

    return (
      normalizedLayerId.includes("boundary") ||
      normalizedLayerId.includes("border") ||
      normalizedLayerId.includes("admin") ||
      sourceLayerName.includes("boundary") ||
      sourceLayerName.includes("admin")
    );
  });
}

/**
 * Determines whether an administrative boundary layer represents a country
 * boundary rather than an internal subdivision boundary.
 *
 * MapTiler identifies its international boundary layer as `Country border`.
 * The filter also normally contains `admin_level = 2`, which provides a
 * fallback if the layer name changes.
 */
function isCountryBoundaryLayer(
  layer: maplibregl.LayerSpecification,
): boolean {
  const normalizedLayerId = layer.id.toLowerCase();

  if (
    normalizedLayerId.includes("country") ||
    normalizedLayerId.includes("international")
  ) {
    return true;
  }

  /*
   * Serializing the style filter lets this helper recognize MapTiler boundary
   * layers whose filter identifies OSM admin_level 2 without coupling this
   * utility to one exact expression representation.
   */
  const filterText = JSON.stringify(
    (layer as { filter?: unknown }).filter ?? null,
  ).toLowerCase();

  return (
    filterText.includes("admin_level") &&
    (filterText.includes("2") || filterText.includes('"2"'))
  );
}

/**
 * Applies visibility to each named MapTiler layer that exists in the current
 * style.
 */
function setNamedLayersVisible(
  map: maplibregl.Map,
  layerIds: ReadonlySet<string>,
  shouldShow: boolean,
): void {
  for (const layerId of layerIds) {
    if (!map.getLayer(layerId)) {
      continue;
    }

    setLayerVisible(map, layerId, shouldShow);
  }
}

/**
 * Sets one style layer's visibility.
 */
function setLayerVisible(
  map: maplibregl.Map,
  layerId: string,
  shouldShow: boolean,
): void {
  map.setLayoutProperty(
    layerId,
    "visibility",
    shouldShow ? "visible" : "none",
  );
}

/**
 * Returns a normalized source-layer name for a MapLibre style layer.
 */
function getSourceLayerName(
  layer: maplibregl.LayerSpecification,
): string {
  const sourceLayer = (
    layer as {
      "source-layer"?: string;
    }
  )["source-layer"];

  return sourceLayer?.toLowerCase() ?? "";
}
