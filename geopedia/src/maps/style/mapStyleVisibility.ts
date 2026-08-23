/**
 * Provides utilities for changing the visibility of layers supplied by the
 * base MapLibre style.
 *
 * These helpers modify layers that come from the external base-map style,
 * such as MapTiler labels and administrative boundaries.
 *
 * GeoPedia's own feature layers are controlled separately.
 */

import type * as maplibregl from "maplibre-gl";

/**
 * Shows or hides all symbol layers supplied by the base-map style.
 *
 * MapLibre styles generally use symbol layers for city names, state names,
 * road labels, water labels, points of interest, and similar map text/icons.
 *
 * @param map - MapLibre map whose base-style labels should be updated.
 * @param shouldShowLabels - Whether base-map symbol layers should be visible.
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

    map.setLayoutProperty(
      layer.id,
      "visibility",
      shouldShowLabels ? "visible" : "none",
    );
  }
}

/**
 * Shows or hides administrative boundary line layers supplied by the
 * base-map style.
 *
 * GeoPedia's own quiz-feature border layer is handled separately. This
 * helper only targets base-style line layers whose ID or source-layer name
 * indicates that they represent administrative boundaries.
 *
 * @param map - MapLibre map whose base-style boundaries should be updated.
 * @param shouldShowBorders - Whether administrative boundary layers should
 * be visible.
 */
export function setBaseMapBordersVisible(
  map: maplibregl.Map,
  shouldShowBorders: boolean,
): void {
  const styleLayers = map.getStyle().layers ?? [];

  for (const layer of styleLayers) {
    if (layer.type !== "line") {
      continue;
    }

    const sourceLayerName = getSourceLayerName(layer);

    const normalizedLayerId = layer.id.toLowerCase();

    const isAdministrativeBoundary =
      normalizedLayerId.includes("boundary") ||
      normalizedLayerId.includes("admin") ||
      sourceLayerName.includes("boundary") ||
      sourceLayerName.includes("admin");

    if (!isAdministrativeBoundary) {
      continue;
    }

    map.setLayoutProperty(
      layer.id,
      "visibility",
      shouldShowBorders ? "visible" : "none",
    );
  }
}

/**
 * Returns a normalized source-layer name for a MapLibre style layer.
 *
 * Not every layer type defines a `source-layer`, so an empty string is
 * returned when the property is unavailable.
 *
 * @param layer - MapLibre style layer being inspected.
 * @returns Lowercase source-layer name, or an empty string when absent.
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
