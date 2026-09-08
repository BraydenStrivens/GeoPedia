/**
 * Owns the lifecycle and base geographic styling of GeoPedia's Home world
 * navigation MapLibre map.
 *
 * This hook is intentionally specific to the world-navigation experience. It:
 *
 * - Creates and destroys the Home MapLibre map instance.
 * - Loads GeoPedia's world-country geographic source and layers.
 * - Marks countries and territories according to GeoGuessr availability.
 * - Colors GeoGuessr and non-GeoGuessr regions differently.
 * - Applies hover colors to countries whose interaction hook enables hover.
 * - Keeps country borders visible and base-map place labels hidden.
 * - Tracks when GeoPedia's world-country source has finished loading.
 *
 * Quiz availability, unavailable-country hatching, hover eligibility, pointer
 * behavior, hover-popup state, and navigation are intentionally handled by
 * `useWorldNavigationInteractions`.
 */

"use client";

import * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect, useRef, useState } from "react";

import {
  FEATURE_FILL_LAYER_ID,
  FEATURE_SOURCE_ID,
} from "@/maps/constants/mapLayerIds";
import { addMapLayers } from "@/maps/layers/mapLayers";
import { createMapStyle } from "@/maps/style/mapStyle";
import { applyBaseMapLayerVisibility } from "@/maps/style/mapStyleVisibility";
import type { MapConfig } from "@/maps/types";

const GEOGUESSR_COUNTRY_FILL_COLOR = "#bae6fd";
const GEOGUESSR_COUNTRY_HOVER_COLOR = "#7dd3fc";

const OTHER_COUNTRY_FILL_COLOR = "#cbd5e1";
const OTHER_COUNTRY_HOVER_COLOR = "#b6c2cf";

/**
 * Dependencies required to create GeoPedia's Home world-navigation map.
 */
type UseWorldNavigationMapParams = {
  /** HTML element into which MapLibre creates the world-navigation map. */
  containerRef: RefObject<HTMLDivElement | null>;

  /** Static world-map configuration containing geometry and camera settings. */
  mapConfig: MapConfig;
};

/**
 * State returned by `useWorldNavigationMap`.
 */
type UseWorldNavigationMapResult = {
  /** MapLibre instance, or `null` before creation and after cleanup. */
  mapRef: RefObject<maplibregl.Map | null>;

  /**
   * Whether GeoPedia's world-country source has finished loading and the
   * navigation-specific base styling is ready for interaction hooks.
   */
  isMapReady: boolean;
};

/**
 * Applies world-navigation-specific country fill styling.
 *
 * GeoGuessr membership controls the normal country color while the existing
 * `hover` feature state controls the temporary hover treatment. The interaction
 * hook only enables hover for countries containing quizzes, keeping visual
 * classification independent from quiz availability.
 *
 * @param map - Ready MapLibre world-navigation map.
 */
function applyWorldNavigationFillStyle(map: maplibregl.Map): void {
  const fillColorExpression: maplibregl.ExpressionSpecification = [
    "case",

    /*
     * Navigable GeoGuessr country currently being hovered.
     */
    [
      "all",
      ["boolean", ["feature-state", "hover"], false],
      ["boolean", ["get", "geoguessr"], false],
    ],
    GEOGUESSR_COUNTRY_HOVER_COLOR,

    /*
     * Navigable non-GeoGuessr country currently being hovered.
     */
    ["boolean", ["feature-state", "hover"], false],
    OTHER_COUNTRY_HOVER_COLOR,

    /*
     * Normal GeoGuessr country or territory.
     */
    ["boolean", ["get", "geoguessr"], false],
    GEOGUESSR_COUNTRY_FILL_COLOR,

    /*
     * Normal country or territory outside GeoGuessr coverage.
     */
    OTHER_COUNTRY_FILL_COLOR,
  ];

  map.setPaintProperty(
    FEATURE_FILL_LAYER_ID,
    "fill-color",
    fillColorExpression,
  );

  /*
   * World-navigation classification relies directly on country color, so keep
   * the geographic fill fully visible rather than using feature-quiz shading
   * opacity.
   */
  map.setPaintProperty(FEATURE_FILL_LAYER_ID, "fill-opacity", 1);
}

/**
 * Creates, configures, and owns GeoPedia's Home world-navigation MapLibre map.
 *
 * The map is recreated only when configuration values that fundamentally define
 * the map instance change. Quiz availability and runtime navigation behavior
 * are intentionally registered separately.
 *
 * @param params - World-map configuration and React-owned map container.
 * @returns MapLibre instance ref and world-country source readiness state.
 */
export function useWorldNavigationMap({
  containerRef,
  mapConfig,
}: UseWorldNavigationMapParams): UseWorldNavigationMapResult {
  /**
   * Stores the imperative MapLibre instance without placing the map object in
   * React state.
   */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /**
   * Signals when the world-country source has loaded and its navigation-specific
   * base styling has been applied.
   */
  const [isMapReady, setIsMapReady] = useState(false);

  /*
   * Extract only configuration values that fundamentally define the MapLibre
   * instance or its geographic layers.
   */
  const { style, initialView, geojsonUrl, promoteId, layers } =
    mapConfig;

  /**
   * Creates, configures, and eventually destroys the world-navigation map.
   */
  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    /*
     * Convert GeoPedia's static map-style configuration into the style
     * representation expected by MapLibre.
     */
    const mapStyle = createMapStyle(style);

    /*
     * Create the Home world-navigation map inside the React-owned container.
     */
    const map = new maplibregl.Map({
      container,
      style: mapStyle,
      center: initialView.center,
      zoom: initialView.zoom,
      minZoom: 1.8,
      attributionControl: false,
    });

    map.doubleClickZoom.disable();
    map.scrollZoom.setWheelZoomRate(1 / 250);

    mapRef.current = map;

    /**
     * Configures GeoPedia's world-country source and layers after the base style
     * becomes available.
     */
    function handleStyleLoad(): void {
      /*
       * Add the shared geographic source, fill layer, and country borders.
       *
       * World navigation always displays both country shading and borders, so
       * these values are fixed rather than controlled by quiz-setting refs.
       */
      addMapLayers(map, {
        geojsonUrl,
        promoteId,
        layers,

        showShading: true,
        showBorders: true,
      });

      /*
       * The Home map intentionally suppresses base-map place labels while
       * retaining geographic/base-map border visibility.
       */
      applyBaseMapLayerVisibility(map, undefined, false, true);

      /**
       * Applies GeoGuessr classification once the world-country GeoJSON source
       * has completely loaded.
       */
      function handleSourceData(
        event: maplibregl.MapSourceDataEvent,
      ): void {
        if (
          event.sourceId !== FEATURE_SOURCE_ID ||
          !event.isSourceLoaded
        ) {
          return;
        }

        applyWorldNavigationFillStyle(map);

        setIsMapReady(true);

        map.off("sourcedata", handleSourceData);
      }

      map.on("sourcedata", handleSourceData);

      /*
       * GeoJSON may occasionally finish loading before the sourcedata listener
       * above is registered. Apply classification immediately in that case.
       */
      if (map.isSourceLoaded(FEATURE_SOURCE_ID)) {
        applyWorldNavigationFillStyle(map);

        setIsMapReady(true);

        map.off("sourcedata", handleSourceData);
      }
    }

    map.on("style.load", handleStyleLoad);

    /**
     * Reports MapLibre runtime errors during development without changing the
     * map lifecycle.
     */
    function handleMapError(event: maplibregl.ErrorEvent): void {
      console.error("MAPLIBRE ERROR:", event.error);
    }

    map.on("error", handleMapError);

    /**
     * Destroys all resources owned by this world-navigation map instance.
     */
    return () => {
      setIsMapReady(false);

      mapRef.current = null;

      map.off("error", handleMapError);

      map.remove();
    };
  }, [
    containerRef,

    style,
    initialView,
    geojsonUrl,
    promoteId,
    layers,
  ]);

  return {
    mapRef,
    isMapReady,
  };
}
