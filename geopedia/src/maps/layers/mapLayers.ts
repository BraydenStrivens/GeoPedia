/**
 * Adds GeoPedia's shared geographic source and visual feature layers to an
 * existing MapLibre map.
 *
 * This module is responsible only for creating:
 *
 * - The GeoJSON feature source.
 * - The normal feature fill layer.
 * - The feature hover layer.
 * - The feature border layer.
 *
 * Click behavior, hover event handling, quiz logic, and other interactions
 * are configured elsewhere.
 */

import type * as maplibregl from "maplibre-gl";

import type { MapLayerConfig } from "@/maps/types";

/**
 * Configuration required to create GeoPedia's shared geographic layers.
 */
type AddMapLayersParams = {
  /** URL of the GeoJSON file used by the map. */
  geojsonUrl: string;

  /** GeoJSON property promoted by MapLibre to `feature.id`. */
  promoteId?: string;

  /** Appearance of the map's fill and border layers. */
  layers: MapLayerConfig;

  /** Whether default feature shading should be visible initially. */
  showShading: boolean;

  /** Whether GeoPedia's feature border layer should be visible initially. */
  showBorders: boolean;
};

/**
 * Adds GeoPedia's feature source and shared visual layers to a MapLibre map.
 *
 * Shading and border settings are applied during initial layer creation so
 * the map can render with the user's persisted settings from its first frame.
 *
 * @param map - MapLibre map receiving the source and layers.
 * @param params - Data and appearance configuration for the feature layers.
 */
export function addMapLayers(
  map: maplibregl.Map,
  {
    geojsonUrl,
    promoteId,
    layers,
    showShading,
    showBorders,
  }: AddMapLayersParams,
): void {
  /**
   * Geographic source shared by all GeoPedia feature layers.
   *
   * promoteId provides the stable IDs required by feature-state operations
   * such as hover highlighting.
   */
  map.addSource("features", {
    type: "geojson",
    data: geojsonUrl,
    promoteId,
  });

  /**
   * Main geographic fill layer.
   *
   * Shading is controlled through fill-color rather than fill-opacity.
   * Keeping opacity constant allows shading to be toggled back on after the
   * map initially loads with shading disabled.
   */
  map.addLayer({
    id: "features-fill",
    type: "fill",
    source: "features",

    paint: {
      "fill-color": showShading
        ? layers.fill.color
        : "rgba(0, 0, 0, 0)",

      "fill-opacity": layers.fill.opacity,

      /*
       * Fill outlines are kept transparent so the border setting can fully
       * remove visible region boundaries.
       */
      "fill-outline-color": "rgba(0, 0, 0, 0)",
    },
  });

  /**
   * Hover overlay layer.
   *
   * The layer itself is always present. Its visibility is controlled by
   * feature-state values set by the interaction system.
   */
  map.addLayer({
    id: "features-hover",
    type: "fill",
    source: "features",

    paint: {
      "fill-color": "#000000",

      "fill-opacity": [
        "case",
        ["boolean", ["feature-state", "hover"], false],
        0.2,
        0,
      ],

      "fill-outline-color": "rgba(0, 0, 0, 0)",
    },
  });

  /**
   * Explicit geographic border layer.
   *
   * Base-map administrative boundaries are controlled separately because
   * they come from the external MapLibre/MapTiler style.
   */
  map.addLayer({
    id: "features-borders",
    type: "line",
    source: "features",

    layout: {
      visibility: showBorders ? "visible" : "none",
    },

    paint: {
      "line-color": layers.borders.color,

      "line-width": layers.borders.width,
    },
  });
}
