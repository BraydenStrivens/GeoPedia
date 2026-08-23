/**
 * Owns the lifecycle of a MapLibre map instance.
 *
 * This custom React hook creates and configures the MapLibre map used by
 * the Map component. It:
 *
 * - Creates the base MapLibre map
 * - Waits for the base style to load
 * - Adds GeoPedia's GeoJSON source and custom layers
 * - Applies initial persisted map-display settings
 * - Registers feature hover and click interactions
 * - Tracks when GeoPedia's feature source is ready
 * - Cleans up the MapLibre instance when necessary
 *
 * React values that may change while the MapLibre instance remains alive
 * are passed as refs. Long-lived MapLibre event handlers can therefore read
 * the latest React values without forcing the entire map to be recreated.
 *
 * The hook returns both the MapLibre map ref and an isMapReady flag so other
 * React effects can safely modify the existing map after its source/layers
 * have finished loading.
 */

import * as maplibregl from "maplibre-gl";
import type React from "react";
import { useEffect, useRef, useState } from "react";

import { setupMapInteractions } from "@/maps/mapInteractions";
import { addMapLayers } from "@/maps/mapLayers";
import { createMapStyle } from "@/maps/mapStyle";
import {
  setBaseMapBordersVisible,
  setBaseMapLabelsVisible,
} from "@/maps/mapStyleVisibility";
import type {
  HoveredFeature,
  IncorrectSelection,
  MapClickBehavior,
  MapConfig,
} from "@/maps/types";
import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

/**
 * Values required by useMap to create the map and connect MapLibre
 * interactions to the surrounding React application.
 */
type UseMapParams = {
  /**
   * React ref containing the HTML element into which MapLibre creates
   * its canvas and map UI.
   */
  containerRef: React.RefObject<HTMLDivElement | null>;

  /**
   * Static configuration describing this map's geographic data, style,
   * initial camera position, layers, and hover appearance.
   */
  mapConfig: MapConfig;

  /**
   * Current runtime click behavior.
   *
   * A ref is used because click behavior can change while the same MapLibre
   * instance remains alive. For example, Show Answers temporarily changes a
   * quiz map from "quiz" to "none".
   */
  clickBehaviorRef: React.RefObject<MapClickBehavior>;

  /**
   * Determines whether feature hover interaction is currently enabled.
   *
   * This can change at runtime when Borders is toggled or Show Answers is
   * entered, so MapLibre handlers read the current value through a ref.
   */
  hoverEnabledRef: React.RefObject<boolean>;

  /**
   * Ref containing the current quiz.
   *
   * Long-lived MapLibre click handlers use this instead of capturing an old
   * quiz value when the event listeners are initially registered.
   */
  quizRef: React.RefObject<Quiz | undefined>;

  /**
   * Ref containing the current Normal/Hard quiz mode.
   *
   * mapInteractions uses this to decide whether fully answered features
   * remain hoverable/clickable in Hard Mode.
   */
  quizModeRef: React.RefObject<QuizMode>;

  /**
   * Ref containing the quiz question currently being asked.
   */
  currentQuestionRef: React.RefObject<QuizQuestion | undefined>;

  /**
   * Ref containing the latest result for every completed quiz answer.
   */
  answerStatusesRef: React.RefObject<Record<string, AnswerStatus>>;

  /**
   * Ref containing the current answerQuestion function.
   */
  answerQuestionRef: React.RefObject<(isCorrect: boolean) => void>;

  /**
   * Callback used by navigation maps when a geographic feature is clicked.
   */
  navigateToCountry: (countryId: string) => void;

  /**
   * Updates the ID of the feature currently being hovered.
   *
   * Show Answers uses this to apply matching hover styling to the answer
   * label associated with that feature.
   */
  setHoveredFeatureId: (featureId: string | null) => void;

  /**
   * Updates the floating feature-name label used by navigation maps.
   */
  setHoveredFeature: (feature: HoveredFeature | null) => void;

  /**
   * Updates temporary incorrect-selection feedback after a user clicks the
   * wrong geographic feature.
   */
  setIncorrectSelection: (selection: IncorrectSelection | null) => void;

  /**
   * Determines whether incorrect selections should display their temporary
   * name popup.
   */
  showIncorrectSelectionRef: React.RefObject<boolean>;

  /**
   * Persisted map-display settings.
   *
   * These refs are read while the MapLibre style is initially loading so the
   * map starts with the user's saved appearance instead of first rendering
   * defaults and then visibly correcting itself.
   */
  showShadingRef: React.RefObject<boolean>;

  showBordersRef: React.RefObject<boolean>;

  showLabelsRef: React.RefObject<boolean>;
};

/**
 * Creates and manages one MapLibre map instance.
 *
 * @returns
 * mapRef:
 *   Ref containing the current MapLibre map, or null before creation/after
 *   cleanup.
 *
 * isMapReady:
 *   True once GeoPedia's "features" source has completely loaded and the
 *   custom feature layers are safe for other React effects to modify.
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
  setHoveredFeature,
  setHoveredFeatureId,
  setIncorrectSelection,

  showIncorrectSelectionRef,

  showShadingRef,
  showBordersRef,
  showLabelsRef,
}: UseMapParams) {
  /**
   * Stores the MapLibre instance without causing React renders when the map
   * object itself changes.
   */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /**
   * Signals when GeoPedia's own feature source has finished loading.
   *
   * React effects in Map.tsx use this before changing fill expressions,
   * borders, labels, and Show Answers markers.
   */
  const [isMapReady, setIsMapReady] = useState(false);

  /*
   * Extract only the static MapConfig values needed to create the map.
   *
   * Runtime settings such as click behavior are intentionally supplied
   * through refs instead so they do not rebuild the MapLibre instance.
   */
  const { style, initialView, geojsonUrl, promoteId, layers, hover } =
    mapConfig;

  /**
   * Creates and destroys the MapLibre instance.
   *
   * This effect should only rerun when something that fundamentally changes
   * the map itself changes, such as:
   *
   * - Map style
   * - Initial view
   * - GeoJSON source
   * - Layer configuration
   * - Map hover configuration
   *
   * Normal quiz state and user-setting changes should NOT recreate the map.
   */
  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    /*
     * Convert GeoPedia's MapStyle configuration into a style object or URL
     * understood by MapLibre.
     */
    const mapStyle = createMapStyle(style);

    /*
     * Create the MapLibre map and attach it to the React-owned container.
     */
    const map = new maplibregl.Map({
      container: containerRef.current,

      style: mapStyle,

      center: initialView.center,

      zoom: initialView.zoom,

      attributionControl: false,
    });

    /*
     * GeoPedia quizzes use rapid feature clicks, so MapLibre's default
     * double-click-to-zoom behavior is disabled.
     */
    map.doubleClickZoom.disable();

    mapRef.current = map;

    /**
     * GeoPedia's source and custom layers cannot be installed until the base
     * MapLibre style has finished loading.
     */
    map.on("style.load", () => {
      /*
       * Add GeoPedia's feature source, fill layer, hover layer, and border
       * layer.
       *
       * Saved Shading/Borders values are read here so the first rendered
       * frame already reflects the user's persisted settings.
       */
      addMapLayers(map, {
        geojsonUrl,
        promoteId,
        layers,
        hover,

        showShading: showShadingRef.current,

        showBorders: showBordersRef.current,
      });

      /*
       * Apply persisted visibility settings to layers supplied by the
       * MapTiler/base-map style before the map is declared ready.
       *
       * This prevents a visible flash of default borders or labels when
       * entering/reloading a quiz.
       */
      setBaseMapBordersVisible(map, showBordersRef.current);

      setBaseMapLabelsVisible(map, showLabelsRef.current);

      /*
       * Register the MapLibre mouse and click handlers.
       *
       * Most changing React values are passed as refs so these handlers can
       * remain installed for the lifetime of the MapLibre map.
       */
      setupMapInteractions({
        map,

        quizRef,
        quizModeRef,

        clickBehaviorRef,
        hover,
        hoverEnabledRef,

        currentQuestionRef,
        answerStatusesRef,
        answerQuestionRef,

        navigateToCountry,

        setIncorrectSelection,
        setHoveredFeature,
        setHoveredFeatureId,

        showIncorrectSelectionRef,
      });

      /**
       * Wait until GeoPedia's "features" GeoJSON source has completely
       * loaded before telling the React side that the map is ready.
       *
       * style.load only guarantees that the base style exists; the
       * asynchronous GeoJSON source may still be loading afterward.
       */
      const handleSourceData = (event: maplibregl.MapSourceDataEvent) => {
        if (event.sourceId === "features" && event.isSourceLoaded) {
          setIsMapReady(true);

          /*
           * This listener is only needed until the initial feature source
           * load finishes.
           */
          map.off("sourcedata", handleSourceData);
        }
      };

      map.on("sourcedata", handleSourceData);
    });

    /**
     * Cleanup runs when this hook unmounts or when one of the static map
     * configuration dependencies changes.
     *
     * map.remove() destroys MapLibre's canvas, event listeners, sources,
     * layers, and other resources owned by this map instance.
     */
    return () => {
      mapRef.current = null;

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
     * These are stable ref objects/callbacks. Their `.current` values can
     * change without causing this lifecycle effect to rerun.
     */
    clickBehaviorRef,
    hoverEnabledRef,

    quizRef,
    quizModeRef,
    currentQuestionRef,
    answerStatusesRef,
    answerQuestionRef,

    navigateToCountry,

    setHoveredFeature,
    setHoveredFeatureId,
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
