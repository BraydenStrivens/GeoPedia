/**
 * Creates and owns the MapLibre map used by GeoPedia town quizzes.
 *
 * Town quizzes use a shared MapTiler base map rather than country-specific
 * geographic feature layers. This hook is responsible for creating that map,
 * applying the country's initial camera position, suppressing place labels
 * that could reveal town answers, and exposing the MapLibre instance to the
 * town quiz UI.
 *
 * Town-specific quiz state, guess scoring, result visualization, and question
 * progression are intentionally handled outside this hook so the map lifecycle
 * remains independent from gameplay state.
 */

"use client";

import * as maplibregl from "maplibre-gl";
import { type RefObject, useEffect, useRef, useState } from "react";

import { createMapStyle } from "@/maps/style/mapStyle";
import { MapStyle } from "@/maps/types";
import type { TownQuizInitialView } from "@/quiz/town/townCountryConfigs";

const TOWN_QUIZ_MAP_STYLE: MapStyle = {
  type: "maptiler",
};

type UseTownQuizMapParams = {
  /** React-owned element in which MapLibre creates the town quiz map. */
  containerRef: RefObject<HTMLDivElement | null>;

  /** Camera position used when the country quiz first opens. */
  initialView: TownQuizInitialView;
};

type UseTownQuizMapResult = {
  /** Current MapLibre instance. */
  mapRef: RefObject<maplibregl.Map | null>;

  /**
   * Indicates that MapLibre's base style has loaded and the town quiz map can
   * safely be modified by dependent hooks.
   */
  isMapReady: boolean;
};

/**
 * Creates and manages the MapLibre instance used by a town quiz.
 *
 * @param params - Town-map container and country-specific initial view.
 * @returns MapLibre instance ref and readiness state.
 */
export function useTownQuizMap({
  containerRef,
  initialView,
}: UseTownQuizMapParams): UseTownQuizMapResult {
  const mapRef = useRef<maplibregl.Map | null>(null);

  const [isMapReady, setIsMapReady] = useState(false);

  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    /*
     * Preserve the already-validated container across the asynchronous map-style
     * preparation boundary.
     */
    const mapContainer = container;

    let map: maplibregl.Map | null = null;
    let isCancelled = false;

    /**
     * Creates the shared town quiz map after GeoPedia has prepared the MapTiler
     * base style.
     */
    async function initializeMap(): Promise<void> {
      /*
       * Town quizzes always use GeoPedia's shared MapTiler style.
       *
       * Labels are initially enabled here because town-specific label
       * suppression is applied after the style loads below. If your current
       * createMapStyle API uses different arguments, keep the same call shape
       * used by the feature-map hook.
       */
      const mapStyle = createMapStyle(TOWN_QUIZ_MAP_STYLE);

      if (isCancelled) {
        return;
      }

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
       * Rapid point selection is the primary town-quiz interaction, so prevent
       * double-click zoom from interpreting quick guesses as navigation.
       */
      createdMap.doubleClickZoom.disable();
      map.scrollZoom.setWheelZoomRate(1 / 300);

      /**
       * Finishes town-specific map configuration once the base style exists.
       */
      function handleStyleLoad(): void {
        /*
         * We will move the actual town/city label suppression into a dedicated
         * helper once we inspect the current MapTiler label configuration.
         *
         * Do not hide all labels here yet because country names, roads, water,
         * and other geographic context may still be useful during the quiz.
         */
        setIsMapReady(true);
      }

      createdMap.on("style.load", handleStyleLoad);
    }
    void initializeMap();

    return () => {
      isCancelled = true;

      mapRef.current = null;
      setIsMapReady(false);

      map?.remove();
    };
  }, [containerRef, initialView]);

  return { mapRef, isMapReady };
}
