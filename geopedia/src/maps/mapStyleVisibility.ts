/**
 * Utilities for changing the visibility of layers that come from the
 * MapLibre base-map style.
 */

import type * as maplibregl from "maplibre-gl";

/**
 * Shows or hides base-map label layers.
 *
 * MapLibre styles generally render labels as "symbol" layers. This includes
 * things such as city names, state names, road names, river names, and POI
 * labels.
 */
export function setBaseMapLabelsVisible(
  map: maplibregl.Map,
  visible: boolean,
) {
  const layers = map.getStyle().layers ?? [];

  for (const layer of layers) {
    if (layer.type !== "symbol") {
      continue;
    }

    map.setLayoutProperty(
      layer.id,
      "visibility",
      visible ? "visible" : "none",
    );
  }
}

/**
 * Shows or hides administrative boundary lines from the base-map style.
 *
 * GeoPedia's own feature border layer is handled separately. This function
 * only targets base-map line layers whose layer ID or source-layer indicates
 * that they represent administrative boundaries.
 */
export function setBaseMapBordersVisible(
  map: maplibregl.Map,
  visible: boolean,
) {
  const layers = map.getStyle().layers ?? [];

  for (const layer of layers) {
    if (layer.type !== "line") {
      continue;
    }

    const sourceLayer = (
      layer as {
        "source-layer"?: string;
      }
    )["source-layer"];

    const layerId = layer.id.toLowerCase();

    const sourceLayerName = sourceLayer?.toLowerCase() ?? "";

    const isAdministrativeBoundary =
      layerId.includes("boundary") ||
      layerId.includes("admin") ||
      sourceLayerName.includes("boundary") ||
      sourceLayerName.includes("admin");

    if (!isAdministrativeBoundary) {
      continue;
    }

    map.setLayoutProperty(
      layer.id,
      "visibility",
      visible ? "visible" : "none",
    );
  }
}
