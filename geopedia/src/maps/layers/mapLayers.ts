/**
 * Adds GeoPedia's shared geographic source and visual feature layers to an
 * existing MapLibre map.
 *
 * This module creates:
 *
 * - The shared geographic GeoJSON source.
 * - The normal geographic fill layer.
 * - The manual-selection overlay.
 * - The feature-hover overlay.
 * - The explicit geographic border layer.
 *
 * Click behavior, hover event handling, quiz logic, active-group filtering,
 * manual-selection filtering, and runtime display synchronization are handled
 * elsewhere.
 */

import type * as maplibregl from "maplibre-gl";

import {
  FEATURE_BORDER_LAYER_ID,
  FEATURE_FILL_LAYER_ID,
  FEATURE_HOVER_LAYER_ID,
  FEATURE_SELECTION_LAYER_ID,
  FEATURE_SOURCE_ID,
} from "@/maps/constants/mapLayerIds";
import type { MapLayerConfig } from "@/maps/types";

/**
 * Configuration required to create GeoPedia's shared geographic source and
 * layers.
 */
type AddMapLayersParams = {
  /** URL of the GeoJSON dataset rendered by the map. */
  geojsonUrl: string;

  /**
   * Optional GeoJSON property promoted by MapLibre to provide stable
   * `feature.id` values.
   */
  promoteId?: string;

  /** Appearance of GeoPedia's geographic fill and border layers. */
  layers: MapLayerConfig;

  /** Whether default geographic feature shading should be visible initially. */
  showShading: boolean;

  /** Whether GeoPedia's explicit geographic border layer is visible initially. */
  showBorders: boolean;
};

/**
 * Adds GeoPedia's geographic source and shared visual layers to a MapLibre map.
 *
 * Shading and border settings are applied during initial layer creation so the
 * first rendered frame already reflects the user's persisted preferences.
 *
 * @param map - MapLibre map receiving the geographic source and layers.
 * @param params - Geographic data, identity, appearance, and initial settings.
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
   * `promoteId` provides the stable feature identity required by hover
   * feature-state, manual grouping, and React-side quiz-group synchronization.
   */
  map.addSource(FEATURE_SOURCE_ID, {
    type: "geojson",
    data: geojsonUrl,
    promoteId,
  });

  /**
   * Main geographic fill layer.
   *
   * Shading is controlled through `fill-color` rather than `fill-opacity`.
   * Keeping opacity constant allows shading to be toggled back on after the map
   * initially loads with shading disabled.
   */
  map.addLayer({
    id: FEATURE_FILL_LAYER_ID,

    type: "fill",

    source: FEATURE_SOURCE_ID,

    paint: {
      "fill-color": showShading
        ? layers.fill.color
        : "rgba(0, 0, 0, 0)",

      "fill-opacity": layers.fill.opacity,

      /*
       * Fill outlines remain transparent so the explicit border layer can
       * completely control whether geographic boundaries are visible.
       */
      "fill-outline-color": "rgba(0, 0, 0, 0)",
    },
  });

  /**
   * Manual-selection overlay.
   *
   * This layer highlights geographic features selected while creating or
   * editing a manual quiz group.
   *
   * The layer starts hidden. `useManualSelectionColors` later makes it visible
   * and applies a feature-ID filter matching the current manual-selection
   * draft.
   *
   * Keeping this overlay separate prevents temporary selection highlighting
   * from modifying normal map shading or quiz-result coloring.
   */
  map.addLayer({
    id: FEATURE_SELECTION_LAYER_ID,

    type: "fill",

    source: FEATURE_SOURCE_ID,

    layout: {
      visibility: "none",
    },

    paint: {
      "fill-color": "#3b82f6",
      "fill-opacity": 0.45,
      "fill-outline-color": "rgba(0, 0, 0, 0)",
    },
  });

  /**
   * Geographic hover overlay.
   *
   * The layer remains present for the lifetime of the map. Visibility for
   * individual features is controlled through MapLibre feature-state values
   * maintained by the interaction system.
   */
  map.addLayer({
    id: FEATURE_HOVER_LAYER_ID,

    type: "fill",

    source: FEATURE_SOURCE_ID,

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
   * Base-map administrative boundaries are controlled separately because they
   * originate from the external MapLibre/MapTiler style rather than GeoPedia's
   * own geographic source.
   */
  map.addLayer({
    id: FEATURE_BORDER_LAYER_ID,

    type: "line",

    source: FEATURE_SOURCE_ID,

    layout: {
      visibility: showBorders ? "visible" : "none",
    },

    paint: {
      "line-color": layers.borders.color,
      "line-width": layers.borders.width,
    },
  });
}
