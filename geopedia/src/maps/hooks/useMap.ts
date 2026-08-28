/**
 * Owns the lifecycle of a MapLibre map instance.
 *
 * This hook creates and configures the MapLibre map used by GeoPedia's shared
 * Map component. It is responsible for:
 *
 * - Creating the base MapLibre map.
 * - Waiting for the base style to become available.
 * - Adding GeoPedia's geographic source and custom layers.
 * - Applying persisted map-display settings before the map becomes visible.
 * - Registering long-lived geographic hover and click interactions.
 * - Tracking when GeoPedia's geographic source has finished loading.
 * - Destroying the MapLibre instance during cleanup.
 *
 * React values that may change during the map's lifetime are supplied through
 * refs. Long-lived MapLibre event handlers can therefore read current React
 * values without requiring the map or its listeners to be recreated.
 */

"use client";

import * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect, useRef, useState } from "react";

import { setupMapInteractions } from "@/maps/interactions/setupMapInteractions";
import {
  addCountryLabelLayers,
  updateCountryLabelFilter,
} from "@/maps/layers/countryLabelLayers";
import { addMapLayers } from "@/maps/layers/mapLayers";
import { addTownLayers } from "@/maps/layers/townLayers";
import { registerPmtilesProtocol } from "@/maps/pmtiles/registerPmtilesProtocol";
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

import { FEATURE_SOURCE_ID } from "../constants/mapLayerIds";

/**
 * Dependencies required to create a MapLibre map and connect it to GeoPedia's
 * React state and interaction system.
 */
type UseMapParams = {
  /*
   * Map creation.
   */

  /** HTML element into which MapLibre creates its canvas and map UI. */
  containerRef: RefObject<HTMLDivElement | null>;

  /** Static configuration describing the map's data, style, camera, and layers. */
  mapConfig: MapConfig;

  /*
   * Runtime interaction state.
   */

  /** Current behavior performed when a geographic feature is clicked. */
  clickBehaviorRef: RefObject<MapClickBehavior>;

  /** Determines whether geographic features currently respond to hovering. */
  hoverEnabledRef: RefObject<boolean>;

  /*
   * Runtime quiz state.
   */

  /** Current quiz associated with the map, when the map is used for a quiz. */
  quizRef: RefObject<Quiz | undefined>;

  /** Current Normal/Hard quiz mode. */
  quizModeRef: RefObject<QuizMode>;

  /** Quiz question currently being asked. */
  currentQuestionRef: RefObject<QuizQuestion | undefined>;

  /** Completed quiz results keyed by answer value. */
  answerStatusesRef: RefObject<Record<string, AnswerStatus>>;

  /** Current function used to submit a geographic quiz answer result. */
  answerQuestionRef: RefObject<(isCorrect: boolean) => void>;

  /*
   * Manual feature selection.
   */

  /** Latest callback used when manual-selection mode toggles a feature. */
  onFeatureSelectRef: RefObject<(featureId: string) => void>;

  /*
   * Interaction callbacks.
   */

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

  /*
   * Runtime display settings.
   */

  /** Determines whether incorrect selections display their answer label. */
  showIncorrectSelectionRef: RefObject<boolean>;

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
type UseMapResult = {
  /** MapLibre instance, or `null` before creation and after cleanup. */
  mapRef: RefObject<maplibregl.Map | null>;

  /**
   * Whether GeoPedia's geographic feature source has finished loading and its
   * custom layers are ready for runtime updates.
   */
  isMapReady: boolean;
};

/**
 * Creates, configures, and owns a MapLibre map instance.
 *
 * The map is recreated only when dependencies that fundamentally define the
 * map change. Runtime quiz state and display settings are supplied through
 * refs so those values can change without rebuilding the MapLibre instance.
 *
 * @param params - Map configuration, runtime refs, and interaction callbacks.
 * @returns MapLibre instance ref and GeoPedia-source readiness state.
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

  onFeatureSelectRef,

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
   * Stores the MapLibre instance without causing React renders when the map
   * object itself changes.
   */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /**
   * Signals when GeoPedia's geographic source has finished loading.
   *
   * Other map hooks use this state before modifying GeoPedia's custom layers.
   */
  const [isMapReady, setIsMapReady] = useState(false);

  /*
   * Only values that fundamentally define the MapLibre instance are extracted
   * from the map configuration. Changing runtime values are supplied through
   * refs instead.
   */
  const {
    style,
    initialView,
    geojsonUrl,
    promoteId,
    layers,
    hover,
    townLabels,
  } = mapConfig;

  /**
   * Creates, configures, and eventually destroys the MapLibre instance.
   *
   * This effect reruns only when something that fundamentally defines the map
   * changes, such as its style, initial camera, geographic source, geographic
   * layer configuration, or hover configuration.
   *
   * Normal quiz state and runtime display-setting changes should not recreate
   * the map.
   */
  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    registerPmtilesProtocol();

    /*
     * Store the already-validated container in a separate constant so TypeScript
     * does not need to reason about the React ref across the async boundary.
     */
    const mapContainer = container;

    let map: maplibregl.Map | null = null;

    let isCancelled = false;

    /**
     * Creates and configures the MapLibre instance after GeoPedia has prepared
     * the base style.
     *
     * MapTiler styles are fetched before map creation so persisted visibility
     * settings and quiz-sensitive label suppression can be applied before the
     * first rendered frame.
     */
    async function initializeMap(): Promise<void> {
      const mapStyle = await createMapStyle(
        style,
        showLabelsRef.current,
      );

      /*
       * The component may have unmounted while the remote MapTiler style was
       * loading.
       */
      if (isCancelled) {
        return;
      }

      /*
       * Use a non-null local variable for the lifetime of map setup.
       *
       * The outer nullable `map` exists only so the effect cleanup can remove the
       * instance if one was successfully created.
       */
      const createdMap = new maplibregl.Map({
        container: mapContainer,
        style: mapStyle,
        center: initialView.center,
        zoom: initialView.zoom,
        attributionControl: false,
      });

      map = createdMap;

      mapRef.current = createdMap;

      /*
       * GeoPedia quizzes rely heavily on rapid geographic feature selection, so
       * disable MapLibre's default double-click-to-zoom behavior.
       */
      createdMap.doubleClickZoom.disable();

      const handleCountryLabelZoom = (): void => {
        updateCountryLabelFilter(createdMap, createdMap.getZoom());
      };

      createdMap.on("zoomend", handleCountryLabelZoom);

      /**
       * Configures GeoPedia-specific functionality after MapLibre's prepared
       * base style has loaded.
       *
       * Sources and layers cannot safely be added before `style.load`.
       */
      function handleStyleLoad(): void {
        /*
         * Add GeoPedia's geographic source and custom layers.
         *
         * Persisted Shading and Borders settings are read before layer creation
         * so the first rendered state already reflects the user's preferences.
         */
        addMapLayers(createdMap, {
          geojsonUrl,
          promoteId,
          layers,
          showShading: showShadingRef.current,
          showBorders: showBordersRef.current,
        });

        /*
         * Add GeoPedia-controlled contextual town labels when this map enables
         * them.
         */
        if (townLabels) {
          addTownLayers(createdMap, townLabels);

          addCountryLabelLayers(createdMap);
          updateCountryLabelFilter(createdMap, createdMap.getZoom());
        }

        /*
         * Apply persisted visibility settings to layers supplied by the base-map
         * style.
         *
         * The initial style was already prepared with these values before map
         * creation. These calls keep runtime layer state consistent after style
         * loading.
         */
        setBaseMapBordersVisible(createdMap, showBordersRef.current);

        setBaseMapLabelsVisible(createdMap, showLabelsRef.current);

        /*
         * Register GeoPedia's long-lived geographic interaction handlers.
         *
         * Changing React values are read through refs so these listeners remain
         * installed for the lifetime of this MapLibre instance.
         */
        setupMapInteractions({
          map: createdMap,
          clickBehaviorRef,
          hover,

          hoverEnabledRef,
          quizRef,
          quizModeRef,
          currentQuestionRef,
          answerStatusesRef,
          answerQuestionRef,
          onFeatureSelectRef,

          navigateToCountry,

          setHoveredFeatureId,
          setHoveredFeature,
          setIncorrectSelection,

          showIncorrectSelectionRef,
        });

        /**
         * Marks GeoPedia's custom map layers ready once the geographic source has
         * completely loaded.
         *
         * `style.load` guarantees that the base style exists, but the GeoJSON
         * source added above may still be loading asynchronously.
         *
         * @param event - MapLibre source-data event.
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

          /* Readiness is only needed for the initial source load. */
          createdMap.off("sourcedata", handleSourceData);
        }

        createdMap.on("sourcedata", handleSourceData);
      }

      createdMap.on("style.load", handleStyleLoad);
    }

    void initializeMap();

    /**
     * Destroys everything owned by this MapLibre instance.
     *
     * Cleanup may run before the asynchronous style fetch finishes. In that
     * situation `map` remains null and no MapLibre instance needs removal.
     */
    return () => {
      isCancelled = true;

      mapRef.current = null;

      setIsMapReady(false);

      map?.remove();
    };
  }, [
    containerRef,

    style,
    initialView,
    geojsonUrl,
    promoteId,
    layers,
    hover,
    townLabels,

    /*
     * These dependencies are stable refs or callbacks. Their `.current` values
     * may change without causing this lifecycle effect to rerun.
     */
    clickBehaviorRef,
    hoverEnabledRef,

    quizRef,
    quizModeRef,
    currentQuestionRef,
    answerStatusesRef,
    answerQuestionRef,

    onFeatureSelectRef,

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
