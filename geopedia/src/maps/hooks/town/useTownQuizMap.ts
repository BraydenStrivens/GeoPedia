/**
 * Owns the lifecycle of the MapLibre map used by GeoPedia town quizzes.
 *
 * Town quizzes use a shared MapTiler base map rather than country-specific
 * geographic feature layers. This hook is responsible for:
 *
 * - Creating and destroying the MapLibre instance.
 * - Applying the country's initial camera position.
 * - Permanently suppressing MapTiler settlement labels that would reveal town
 *   quiz answers.
 * - Applying the Show Labels setting to the remaining contextual base-map
 *   labels.
 * - Exposing the MapLibre instance and readiness state to dependent town-quiz
 *   hooks.
 *
 * GeoPedia's custom quiz-town labels are created by separate town-label hooks.
 * They are therefore not controlled by Show Labels; their visibility is
 * controlled independently by the town quiz mode.
 *
 * Town-specific gameplay state, guess scoring, result visualization, and
 * question progression are intentionally handled outside this hook so the map
 * lifecycle remains independent from gameplay state.
 */

"use client";

import * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect, useRef, useState } from "react";

import { useLatestRef } from "@/maps/hooks/useLatestRef";
import { createMapStyle } from "@/maps/style/mapStyle";
import type { MapStyle } from "@/maps/types";
import type { TownQuizInitialView } from "@/quiz/town/townCountryConfigs";

/**
 * Shared base-map style used by every town quiz.
 */
const TOWN_QUIZ_MAP_STYLE: MapStyle = {
  type: "maptiler",
};

/**
 * MapTiler settlement-label layers that must always remain hidden during town
 * quizzes because they could directly reveal quiz answers.
 */
const TOWN_QUIZ_ANSWER_LABEL_LAYER_IDS = new Set<string>([
  "Capital city labels",
  "City labels",
  "Town labels",
  "Place labels",
]);

/**
 * Original visibility state of MapTiler's base-map symbol layers.
 */
type BaseLabelVisibilityMap = Map<
  string,
  maplibregl.VisibilitySpecification
>;

/**
 * Parameters required to create a town quiz map.
 */
type UseTownQuizMapParams = {
  /** React-owned element in which MapLibre creates the town quiz map. */
  containerRef: RefObject<HTMLDivElement | null>;

  /** Camera position used when the country quiz first opens. */
  initialView: TownQuizInitialView;

  /**
   * Whether contextual base-map labels should be visible.
   *
   * This affects base-map labels only. GeoPedia's custom quiz-town answer
   * labels are controlled separately by the town quiz mode.
   */
  showLabels: boolean;
};

/**
 * Result returned by `useTownQuizMap`.
 */
type UseTownQuizMapResult = {
  /** MapLibre instance, or `null` before creation and after cleanup. */
  mapRef: RefObject<maplibregl.Map | null>;

  /**
   * Whether the MapTiler base style has loaded and dependent town-map hooks may
   * safely add or modify layers.
   */
  isMapReady: boolean;
};

/**
 * Captures the original visibility of every symbol layer in the loaded
 * MapTiler base style.
 *
 * MapLibre styles may intentionally contain symbol layers whose visibility is
 * `none`. Remembering each original state allows Show Labels to restore the
 * style faithfully rather than assuming every symbol layer should be visible.
 *
 * This must run before GeoPedia changes any base-label visibility.
 *
 * @param map - Town quiz map whose base style has loaded.
 * @param visibilityMap - Mutable map receiving original layer visibility.
 */
function captureBaseLabelVisibility(
  map: maplibregl.Map,
  visibilityMap: BaseLabelVisibilityMap,
): void {
  const style = map.getStyle();

  if (!style) {
    return;
  }

  visibilityMap.clear();

  for (const layer of style.layers ?? []) {
    if (layer.type !== "symbol") {
      continue;
    }

    const visibility = map.getLayoutProperty(layer.id, "visibility");

    visibilityMap.set(
      layer.id,
      visibility === "none" ? "none" : "visible",
    );
  }
}

/**
 * Applies GeoPedia's town-quiz base-label visibility rules.
 *
 * Answer-revealing MapTiler settlement layers always remain hidden. Every
 * other base-map symbol layer either returns to its original MapTiler
 * visibility or is hidden according to Show Labels.
 *
 * GeoPedia's custom town-label layers are added after the base style is
 * captured and are therefore unaffected by this function.
 *
 * @param map - Town quiz MapLibre instance.
 * @param visibilityMap - Original base-layer visibility snapshot.
 * @param showLabels - Whether contextual base-map labels should be visible.
 */
function applyTownQuizBaseLabelVisibility(
  map: maplibregl.Map,
  visibilityMap: ReadonlyMap<
    string,
    maplibregl.VisibilitySpecification
  >,
  showLabels: boolean,
): void {
  for (const [layerId, originalVisibility] of visibilityMap) {
    if (!map.getLayer(layerId)) {
      continue;
    }

    if (TOWN_QUIZ_ANSWER_LABEL_LAYER_IDS.has(layerId)) {
      map.setLayoutProperty(layerId, "visibility", "none");
      continue;
    }

    map.setLayoutProperty(
      layerId,
      "visibility",
      showLabels ? originalVisibility : "none",
    );
  }
}

/**
 * Creates, configures, and owns the MapLibre map used by a town quiz.
 *
 * Map creation depends only on values that fundamentally define the map.
 * Runtime Show Labels changes are applied to the existing MapLibre instance
 * rather than recreating it.
 *
 * @param params - Town-map container, initial view, and display settings.
 * @returns MapLibre instance ref and readiness state.
 */
export function useTownQuizMap({
  containerRef,
  initialView,
  showLabels,
}: UseTownQuizMapParams): UseTownQuizMapResult {
  /**
   * Stores the imperative MapLibre instance without placing it in React state.
   */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /**
   * Signals when the MapTiler base style has loaded and dependent town-map
   * hooks may safely add or modify layers.
   */
  const [isMapReady, setIsMapReady] = useState(false);

  /**
   * Stores the original visibility of every MapTiler symbol layer.
   *
   * GeoPedia town-label layers are added later and are intentionally absent
   * from this snapshot.
   */
  const baseLabelVisibilityRef = useRef<BaseLabelVisibilityMap>(
    new Map(),
  );

  /**
   * Provides asynchronous MapLibre callbacks with the latest Show Labels value
   * without making map creation depend on that setting.
   */
  const showLabelsRef = useLatestRef(showLabels);

  /**
   * Creates, configures, and eventually destroys the MapLibre instance.
   */
  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    const baseLabelVisibility = baseLabelVisibilityRef.current;

    const mapStyle = createMapStyle(TOWN_QUIZ_MAP_STYLE);

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
     * Finalizes town-map setup once MapLibre's base style has loaded.
     *
     * Original visibility is captured before GeoPedia suppresses any labels so
     * Show Labels can later restore MapTiler's original state faithfully.
     */
    function handleStyleLoad(): void {
      captureBaseLabelVisibility(map, baseLabelVisibility);

      applyTownQuizBaseLabelVisibility(
        map,
        baseLabelVisibility,
        showLabelsRef.current,
      );

      setIsMapReady(true);
    }

    map.on("style.load", handleStyleLoad);

    map.on("error", (event) => {
      console.error("MAPLIBRE ERROR:", event.error);
    });

    return () => {
      setIsMapReady(false);

      baseLabelVisibility.clear();

      mapRef.current = null;

      map.remove();
    };
  }, [containerRef, initialView, showLabelsRef]);

  /**
   * Synchronizes contextual base-map label visibility with Show Labels.
   *
   * The existing MapLibre instance is updated in place rather than recreated.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!map || !isMapReady) {
      return;
    }

    applyTownQuizBaseLabelVisibility(
      map,
      baseLabelVisibilityRef.current,
      showLabels,
    );
  }, [isMapReady, showLabels]);

  return {
    mapRef,
    isMapReady,
  };
}
