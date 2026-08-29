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
import { addMapLayers } from "@/maps/layers/mapLayers";
import { createMapStyle } from "@/maps/style/mapStyle";
import { applyBaseMapLayerVisibility } from "@/maps/style/mapStyleVisibility";
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
 * Configures MapTiler place labels to show a Latin/English name together with
 * the native-script name when MapTiler provides both forms.
 *
 * The existing MapTiler layers retain all of their original placement,
 * collision, ranking, zoom, font-size, and marker behavior. Only their
 * `text-field` expressions are changed.
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
       * non-Latin writing system. In that case, display the Latin name first and
       * the native-script name underneath it.
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
        ["get", "name:latin"],
        ["get", "name:en"],
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
    baseMapLayers,
    initialView,
    geojsonUrl,
    promoteId,
    layers,
    hover,
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

    /*
     * Convert GeoPedia's map-style configuration into the representation
     * expected by MapLibre.
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
     * GeoPedia quizzes rely heavily on rapid geographic feature selection, so
     * disable MapLibre's default double-click-to-zoom behavior.
     */
    map.doubleClickZoom.disable();

    mapRef.current = map;

    /**
     * Configures GeoPedia-specific map functionality after MapLibre's base
     * style has loaded.
     *
     * Sources and layers cannot safely be added before `style.load`.
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
       * Persisted Shading and Borders settings are read before layer creation
       * so the first rendered state already reflects the user's preferences.
       */
      addMapLayers(map, {
        geojsonUrl,
        promoteId,
        layers,

        showShading: showShadingRef.current,

        showBorders: showBordersRef.current,
      });

      /*
       * Apply persisted visibility settings to layers supplied by the base-map
       * style before the map is declared ready.
       */
      applyBaseMapLayerVisibility(
        map,
        baseMapLayers,
        showLabelsRef.current,
        showBordersRef.current,
      );

      /*
       * Register GeoPedia's long-lived geographic interaction handlers.
       *
       * Changing React values are read through refs so these listeners remain
       * installed for the lifetime of this MapLibre instance.
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

        /*
         * Readiness is only needed for the initial source load. Remove the
         * listener once that state has been reached.
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
     * changes and this effect must create a replacement map.
     */
    return () => {
      mapRef.current = null;

      setIsMapReady(false);

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
    hover,

    /*
     * These dependencies are stable refs or callbacks. Their `.current`
     * values may change without causing this lifecycle effect to rerun.
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
