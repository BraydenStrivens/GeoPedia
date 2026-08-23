/**
 * Owns the lifecycle of a MapLibre map instance.
 *
 * This hook creates and configures the MapLibre map used by GeoPedia's shared
 * Map component. It:
 *
 * - Creates the base MapLibre map.
 * - Waits for the base style to load.
 * - Adds GeoPedia's geographic source and custom layers.
 * - Applies persisted map-display settings before the map becomes visible.
 * - Registers feature hover and click interactions.
 * - Tracks when GeoPedia's geographic source is ready.
 * - Destroys the MapLibre instance when necessary.
 *
 * React values that may change during the map's lifetime are provided through
 * refs. Long-lived MapLibre event handlers can therefore read current React
 * values without requiring the map or its listeners to be recreated.
 */

import * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect, useRef, useState } from "react";

import { setupMapInteractions } from "@/maps/interactions/setupMapInteractions";
import { addMapLayers } from "@/maps/layers/mapLayers";
import { createMapStyle } from "@/maps/style/mapStyle";
import {
  setBaseMapBordersVisible,
  setBaseMapLabelsVisible,
} from "@/maps/style/mapStyleVisibility";
import type {
  HoveredFeature,
  IncorrectSelection,
  MapClickBehavior,
  MapConfig,
} from "@/maps/types";
import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

/**
 * Dependencies required to create a MapLibre map and connect it to GeoPedia's
 * React state and interaction system.
 */
type UseMapParams = {
  /** HTML element into which MapLibre creates its canvas and map UI. */
  containerRef: RefObject<HTMLDivElement | null>;

  /** Static configuration describing the map's data, style, camera, and layers. */
  mapConfig: MapConfig;

  /** Current behavior performed when a geographic feature is clicked. */
  clickBehaviorRef: RefObject<MapClickBehavior>;

  /** Determines whether geographic features currently respond to hovering. */
  hoverEnabledRef: RefObject<boolean>;

  /** Current quiz associated with the map, when the map is used for a quiz. */
  quizRef: RefObject<Quiz | undefined>;

  /** Current Normal/Hard quiz mode. */
  quizModeRef: RefObject<QuizMode>;

  /** Quiz question currently being asked. */
  currentQuestionRef: RefObject<QuizQuestion | undefined>;

  /** Completed quiz results keyed by answer value. */
  answerStatusesRef: RefObject<Record<string, AnswerStatus>>;

  /** Current function used to submit a quiz answer result. */
  answerQuestionRef: RefObject<(isCorrect: boolean) => void>;

  /** Navigates to the country represented by a navigation-map feature. */
  navigateToCountry: (countryId: string) => void;

  /** Updates the ID of the geographic feature currently being hovered. */
  setHoveredFeatureId: (featureId: string | null) => void;

  /** Updates the floating feature-name label used by navigation maps. */
  setHoveredFeature: (feature: HoveredFeature | null) => void;

  /** Updates temporary feedback displayed after an incorrect selection. */
  setIncorrectSelection: (
    selection: IncorrectSelection | null,
  ) => void;

  /** Determines whether incorrect selections display their answer label. */
  showIncorrectSelectionRef: RefObject<boolean>;

  /** Determines whether GeoPedia's geographic feature shading is visible. */
  showShadingRef: RefObject<boolean>;

  /** Determines whether geographic and base-map administrative borders are visible. */
  showBordersRef: RefObject<boolean>;

  /** Determines whether labels supplied by the base-map style are visible. */
  showLabelsRef: RefObject<boolean>;
};

/**
 * Result returned by `useMap`.
 */
type UseMapResult = {
  // MapLibre instance, or null before creation and after cleanup.
  mapRef: RefObject<maplibregl.Map | null>;

  // Whether GeoPedia's geographic feature source has finished loading.
  isMapReady: boolean;
};

/**
 * Creates and manages a MapLibre map instance.
 *
 * The map is recreated only when dependencies that fundamentally define the
 * map change. Runtime quiz state and display settings are supplied through
 * refs so they can change without rebuilding the MapLibre instance.
 *
 * @param params - Map configuration, current-value refs, and interaction
 * callbacks required by the map.
 * @returns The MapLibre map ref and its GeoPedia-source readiness state.
 */
export function useMap({
  containerRef,
  mapConfig,

  clickBehaviorRef,
  hoverEnabledRef,

  quizRef,
  quizModeRef,
  currentQuestionRef,
  answerStatusesRef,
  answerQuestionRef,

  navigateToCountry,
  setHoveredFeatureId,
  setHoveredFeature,
  setIncorrectSelection,

  showIncorrectSelectionRef,

  showShadingRef,
  showBordersRef,
  showLabelsRef,
}: UseMapParams): UseMapResult {
  /**
   * Stores the MapLibre instance without causing a React render when the map
   * object itself changes.
   */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /**
   * Signals when GeoPedia's geographic feature source has finished loading.
   *
   * React effects in Map.tsx use this before modifying feature colors,
   * borders, labels, or Show Answers markers.
   */
  const [isMapReady, setIsMapReady] = useState(false);

  /*
   * Only static values that fundamentally define the map are extracted here.
   * Changing runtime values are supplied through refs instead.
   */
  const { style, initialView, geojsonUrl, promoteId, layers, hover } =
    mapConfig;

  /**
   * Creates, configures, and eventually destroys the MapLibre instance.
   *
   * This effect reruns only when something that fundamentally defines the map
   * changes, such as its style, camera, geographic source, layer appearance,
   * or hover configuration.
   *
   * Normal quiz state and runtime setting changes should not recreate the map.
   */
  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    /*
     * Convert GeoPedia's MapStyle configuration into a style representation
     * understood by MapLibre.
     */
    const mapStyle = createMapStyle(style);

    /*
     * Create the MapLibre map inside the React-owned container.
     */
    const map = new maplibregl.Map({
      container,
      style: mapStyle,
      center: initialView.center,
      zoom: initialView.zoom,
      attributionControl: false,
    });

    /*
     * GeoPedia quizzes rely heavily on rapid feature selection, so the
     * default double-click-to-zoom interaction is disabled.
     */
    map.doubleClickZoom.disable();

    mapRef.current = map;

    /**
     * Configures GeoPedia's map-specific functionality after MapLibre's base
     * style becomes available.
     *
     * Sources and layers cannot safely be added before `style.load`.
     */
    function handleStyleLoad() {
      /*
       * Add GeoPedia's geographic source and custom fill, hover, and border
       * layers.
       *
       * Persisted Shading and Borders values are read before layer creation so
       * the first rendered state already reflects the user's saved settings.
       */
      addMapLayers(map, {
        geojsonUrl,
        promoteId,
        layers,

        showShading: showShadingRef.current,

        showBorders: showBordersRef.current,
      });

      /*
       * Apply persisted settings to layers supplied by the base-map style
       * before the map is declared ready.
       *
       * Doing this during initial setup prevents a visible flash of default
       * administrative borders or labels.
       */
      setBaseMapBordersVisible(map, showBordersRef.current);

      setBaseMapLabelsVisible(map, showLabelsRef.current);

      /*
       * Register long-lived feature hover and click handlers.
       *
       * Changing React values are read through refs so these handlers can
       * remain installed for the lifetime of this MapLibre instance.
       */
      setupMapInteractions({
        map,

        clickBehaviorRef,
        hover,
        hoverEnabledRef,

        quizRef,
        quizModeRef,
        currentQuestionRef,
        answerStatusesRef,
        answerQuestionRef,

        navigateToCountry,
        setHoveredFeatureId,
        setHoveredFeature,
        setIncorrectSelection,

        showIncorrectSelectionRef,
      });

      /**
       * Marks the map ready once GeoPedia's geographic source has completely
       * loaded.
       *
       * `style.load` guarantees that the base style exists, but the GeoJSON
       * source added above may still be loading asynchronously.
       */
      function handleSourceData(
        event: maplibregl.MapSourceDataEvent,
      ) {
        if (event.sourceId !== "features" || !event.isSourceLoaded) {
          return;
        }

        setIsMapReady(true);

        /*
         * Readiness is only needed for the initial source load, so remove the
         * listener after that state has been reached.
         */
        map.off("sourcedata", handleSourceData);
      }

      map.on("sourcedata", handleSourceData);
    }

    map.on("style.load", handleStyleLoad);

    /**
     * Destroys everything owned by this MapLibre instance.
     *
     * Cleanup runs when the component unmounts or when a static map dependency
     * changes and this effect needs to create a replacement map.
     */
    return () => {
      mapRef.current = null;

      setIsMapReady(false);

      map.remove();
    };
  }, [
    containerRef,

    style,
    initialView,
    geojsonUrl,
    promoteId,
    layers,
    hover,

    /*
     * These dependencies are stable refs or callbacks. Their `.current`
     * values can change without causing this lifecycle effect to rerun.
     */
    clickBehaviorRef,
    hoverEnabledRef,

    quizRef,
    quizModeRef,
    currentQuestionRef,
    answerStatusesRef,
    answerQuestionRef,

    navigateToCountry,
    setHoveredFeatureId,
    setHoveredFeature,
    setIncorrectSelection,

    showIncorrectSelectionRef,

    showShadingRef,
    showBordersRef,
    showLabelsRef,
  ]);

  return {
    mapRef,
    isMapReady,
  };
}
