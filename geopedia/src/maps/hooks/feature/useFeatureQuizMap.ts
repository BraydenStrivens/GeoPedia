/**
 * Owns the lifecycle of a GeoPedia MapLibre map instance.
 *
 * This hook contains only behavior shared by GeoPedia's different map
 * experiences. It is responsible for:
 *
 * - Creating the base MapLibre map.
 * - Waiting for the base style to become available.
 * - Adding GeoPedia's geographic source and custom layers.
 * - Configuring MapTiler place-name labels.
 * - Applying initial map-display settings.
 * - Tracking when GeoPedia's geographic source has finished loading.
 * - Destroying the MapLibre instance during cleanup.
 *
 * Interaction behavior is intentionally not registered here.
 *
 * Quiz maps and the world-navigation map use different interaction systems,
 * which are installed independently after this hook reports the map ready.
 */

"use client";

import * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect, useRef, useState } from "react";

import { FEATURE_SOURCE_ID } from "@/maps/constants/mapLayerIds";
import { addMapLayers } from "@/maps/layers/mapLayers";
import { createMapStyle } from "@/maps/style/mapStyle";
import { applyBaseMapLayerVisibility } from "@/maps/style/mapStyleVisibility";
import type { MapConfig } from "@/maps/types";

/**
 * Dependencies required to create and initialize a GeoPedia MapLibre map.
 */
type UseFeatureQuizMapParams = {
  /** HTML element into which MapLibre creates its canvas and map UI. */
  containerRef: RefObject<HTMLDivElement | null>;

  /** Static configuration describing the map's data, style, camera, and layers. */
  mapConfig: MapConfig;

  /** Determines whether GeoPedia's geographic feature shading is visible. */
  showShadingRef: RefObject<boolean>;

  /** Determines whether geographic and base-map borders are visible. */
  showBordersRef: RefObject<boolean>;

  /** Determines whether labels supplied by the base-map style are visible. */
  showLabelsRef: RefObject<boolean>;
};

/**
 * Result returned by `useMap`.
 */
type UseFeatureQuizMapResult = {
  /** MapLibre instance, or `null` before creation and after cleanup. */
  mapRef: RefObject<maplibregl.Map | null>;

  /**
   * Whether GeoPedia's geographic feature source has finished loading and its
   * custom layers are ready for runtime hooks and interactions.
   */
  isMapReady: boolean;
};

/**
 * Configures MapTiler place labels to show a Latin/English name together with
 * the native-script name when MapTiler provides both forms.
 *
 * The existing MapTiler layers retain all of their original placement,
 * collision, ranking, zoom, font-size, and marker behavior. Only their
 * `text-field` expressions are changed.
 *
 * @param map - MapLibre map whose MapTiler place labels should be configured.
 */
function configureBaseMapPlaceNames(map: maplibregl.Map): void {
  const placeLabelLayerIds = [
    "Country labels",
    "State labels",
    "Capital city labels",
    "City labels",
    "Town labels",
    "Place labels",
  ];

  const bilingualNameExpression: maplibregl.ExpressionSpecification =
    [
      "case",

      /*
       * MapTiler supplies `name:nonlatin` for places whose native name uses a
       * non-Latin writing system. Display the Latin name first and the native
       * script underneath it.
       */
      ["has", "name:nonlatin"],
      [
        "concat",
        [
          "coalesce",
          ["get", "name:latin"],
          ["get", "name:en"],
          ["get", "name"],
        ],
        "\n",
        ["get", "name:nonlatin"],
      ],

      /* Places without a non-Latin native name remain single-line labels. */
      [
        "coalesce",
        ["get", "name:en"],
        ["get", "name:latin"],
        ["get", "name"],
      ],
    ];

  for (const layerId of placeLabelLayerIds) {
    if (!map.getLayer(layerId)) {
      continue;
    }

    map.setLayoutProperty(
      layerId,
      "text-field",
      bilingualNameExpression,
    );
  }
}

/**
 * Creates, configures, and owns a MapLibre map instance.
 *
 * The map is recreated only when dependencies that fundamentally define the
 * map change. Runtime interaction systems are registered separately by the
 * component using this hook.
 *
 * @param params - Map configuration and initial display-setting refs.
 * @returns MapLibre instance ref and GeoPedia-source readiness state.
 */
export function useFeatureQuizMap({
  containerRef,
  mapConfig,
  showShadingRef,
  showBordersRef,
  showLabelsRef,
}: UseFeatureQuizMapParams): UseFeatureQuizMapResult {
  /**
   * Stores the MapLibre instance without causing React renders when the map
   * object itself changes.
   */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /**
   * Signals when GeoPedia's geographic source has finished loading.
   *
   * Other map hooks wait for this state before modifying GeoPedia's custom
   * source or layers.
   */
  const [isMapReady, setIsMapReady] = useState(false);

  /*
   * Only values that fundamentally define the MapLibre instance are extracted
   * from the map configuration.
   */
  const {
    style,
    baseMapLayers,
    initialView,
    geojsonUrl,
    promoteId,
    layers,
  } = mapConfig;

  /** Creates, configures, and eventually destroys the MapLibre instance. */
  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    /*
     * Convert GeoPedia's map-style configuration into the representation
     * expected by MapLibre.
     */
    const mapStyle = createMapStyle(style);

    /* Create the MapLibre map inside the React-owned container. */
    const map = new maplibregl.Map({
      container,
      style: mapStyle,
      center: initialView.center,
      zoom: initialView.zoom,
      attributionControl: false,
    });

    /*
     * GeoPedia's map experiences use direct single-feature selection heavily,
     * so disable MapLibre's default double-click-to-zoom interaction.
     */
    map.doubleClickZoom.disable();
    map.scrollZoom.setWheelZoomRate(1 / 300);

    mapRef.current = map;

    /**
     * Configures GeoPedia-specific map functionality after MapLibre's base
     * style has loaded.
     */
    function handleStyleLoad(): void {
      /*
       * Configure MapTiler's existing place labels before adding GeoPedia's
       * geographic layers.
       */
      configureBaseMapPlaceNames(map);

      /*
       * Add GeoPedia's geographic source and custom layers.
       *
       * Initial Shading and Borders settings are read before layer creation so
       * the first rendered state already reflects the desired configuration.
       */
      addMapLayers(map, {
        geojsonUrl,
        promoteId,
        layers,

        showShading: showShadingRef.current,

        showBorders: showBordersRef.current,
      });

      /*
       * Apply initial visibility settings to layers supplied by the base-map
       * style.
       */
      applyBaseMapLayerVisibility(
        map,
        baseMapLayers,
        showLabelsRef.current,
        showBordersRef.current,
      );

      /**
       * Marks GeoPedia's custom map layers ready once the geographic source has
       * completely loaded.
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

        setIsMapReady(true);

        map.off("sourcedata", handleSourceData);
      }

      map.on("sourcedata", handleSourceData);

      /*
       * GeoJSON may occasionally finish loading before the sourcedata listener
       * above is registered. Handle that state immediately as well.
       */
      if (map.isSourceLoaded(FEATURE_SOURCE_ID)) {
        setIsMapReady(true);

        map.off("sourcedata", handleSourceData);
      }
    }

    map.on("style.load", handleStyleLoad);

    map.on("error", (event) => {
      console.error("MAPLIBRE ERROR:", event.error);
    });

    /**
     * Destroys everything owned by this MapLibre instance.
     */
    return () => {
      setIsMapReady(false);

      mapRef.current = null;

      map.remove();
    };
  }, [
    containerRef,

    style,
    baseMapLayers,
    initialView,
    geojsonUrl,
    promoteId,
    layers,

    /* These refs remain stable while their `.current` values may change. */
    showShadingRef,
    showBordersRef,
    showLabelsRef,
  ]);

  return {
    mapRef,
    isMapReady,
  };
}
