/**
 * Owns the lifecycle of a MapLibre map instance.
 *
 * This custom React hook creates and configures the MapLibre map used by
 * the Map component. It creates the base map, waits for its style to load,
 * adds GeoPedia's geographic layers and interactions, installs navigation
 * controls, and cleans up the map when necessary.
 *
 * React values that need to remain current inside long-lived MapLibre event
 * handlers are passed into this hook as refs. This allows the event handlers
 * to access current quiz state without requiring the entire map to be
 * recreated whenever that state changes.
 *
 * The hook returns a ref to the MapLibre map so other React effects can
 * modify the existing map, such as updating feature colors after quiz
 * answers change.
 */

import * as maplibregl from "maplibre-gl";
import type React from "react";
import { useEffect, useRef, useState } from "react";

import { setupMapInteractions } from "@/maps/mapInteractions";
import { addMapLayers } from "@/maps/mapLayers";
import { createMapStyle } from "@/maps/mapStyle";
import type {
  HoveredFeature,
  MapClickBehavior,
  MapConfig,
} from "@/maps/types";
import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";

/**
 * Values required by useMap to create the map and connect MapLibre
 * interactions to the surrounding React application.
 */
type UseMapParams = {
  /**
   * Reference to the HTML element that MapLibre will use as its
   * map container.
   */
  containerRef: React.RefObject<HTMLDivElement | null>;

  /**
   * Configuration describing the map's data, appearance, initial
   * camera position, and interaction settings.
   */
  mapConfig: MapConfig;

  /**
   * Describes what happens when a map feature is clicked. Used to differentiate maps
   * that answer quiz questions, navigate to a page, or do nothing when a feature
   * is clicked.
   */
  clickBehavior: MapClickBehavior;

  /**
   * Ref containing the current quiz.
   *
   * A ref is used so MapLibre's long-lived click handlers can access
   * the latest quiz without recreating the map when the quiz changes.
   */
  quizRef: React.RefObject<Quiz | undefined>;

  /**
   * Ref containing the latest question.
   */
  currentQuestionRef: React.RefObject<QuizQuestion | undefined>;

  /**
   * Ref containing the latest result for each answered quiz feature.
   */
  answerStatusesRef: React.RefObject<Record<string, AnswerStatus>>;

  /**
   * Ref containing the latest quiz answer function.
   */
  answerQuestionRef: React.RefObject<(isCorrect: boolean) => void>;

  /**
   * Callback used when a navigation map feature is clicked.
   */
  navigateToCountry: (countryId: string) => void;

  /**
   * Updates the React state used to display the floating hover label.
   */
  setHoveredFeature: (feature: HoveredFeature | null) => void;
};

/**
 * Creates and manages a MapLibre map instance.
 *
 * @returns A ref containing the current MapLibre map instance, or null
 * when the map has not yet been created or has been removed.
 */
export function useMap({
  containerRef,
  mapConfig,
  clickBehavior,
  quizRef,
  currentQuestionRef,
  answerStatusesRef,
  answerQuestionRef,
  navigateToCountry,
  setHoveredFeature,
}: UseMapParams) {
  const mapRef = useRef<maplibregl.Map | null>(null);

  const [isMapReady, setIsMapReady] = useState(false);

  // Extract the configuration values used by the map lifecycle effect.
  const { style, initialView, geojsonUrl, promoteId, layers, hover } =
    mapConfig;

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    setIsMapReady(false);

    /*
     * Convert GeoPedia's MapStyle configuration into the format expected
     * by MapLibre.
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

    map.doubleClickZoom.disable();

    mapRef.current = map;

    map.on("style.load", () => {
      addMapLayers(map, {
        geojsonUrl,
        promoteId,
        layers,
        hover,
      });

      /*
       * GeoPedia's source and layers cannot be added until MapLibre has
       * finished loading the base style.
       *
       * Once the style is ready, add the geographic data and register the
       * mouse/click interactions that operate on those layers.
       */
      setupMapInteractions({
        map,
        clickBehavior,
        hover,
        quizRef,
        currentQuestionRef,
        answerStatusesRef,
        answerQuestionRef,
        navigateToCountry,
        setHoveredFeature,
      });

      const handleSourceData = (event: maplibregl.MapSourceDataEvent) => {
        if (event.sourceId === "features" && event.isSourceLoaded) {
          setIsMapReady(true);

          map.off("sourcedata", handleSourceData);
        }
      };

      map.on("sourcedata", handleSourceData);
    });

    /*
     * React runs this cleanup before the effect runs again and when the
     * component using this hook unmounts.
     *
     * map.remove() destroys the MapLibre instance and removes its event
     * listeners, controls, canvas, and other resources.
     */
    return () => {
      setIsMapReady(false);
      mapRef.current = null;
      map.remove();
    };
  }, [
    containerRef,
    style,
    initialView,
    geojsonUrl,
    promoteId,
    clickBehavior,
    layers,
    hover,
    quizRef,
    currentQuestionRef,
    answerStatusesRef,
    answerQuestionRef,
    navigateToCountry,
    setHoveredFeature,
  ]);

  return {
    mapRef,
    isMapReady,
  };
}
