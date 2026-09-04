/**
 * Creates and owns the MapLibre map used by GeoPedia town quizzes.
 *
 * Town quizzes use a shared MapTiler base map rather than country-specific
 * geographic feature layers. This hook is responsible for:
 *
 * - Creating and destroying the MapLibre instance.
 * - Applying the country's initial camera position.
 * - Permanently suppressing MapTiler settlement labels that would reveal town
 *   quiz answers.
 * - Applying the persisted Show Labels setting to the remaining contextual
 *   base-map labels.
 * - Exposing the MapLibre instance and readiness state to dependent town-quiz
 *   hooks.
 *
 * GeoPedia's custom quiz-town labels are created by separate town-label hooks.
 * They are therefore not controlled by Show Labels; their visibility is
 * controlled independently by Normal and Hard quiz modes.
 *
 * Town-specific gameplay state, guess scoring, result visualization, and
 * question progression are intentionally handled outside this hook so the map
 * lifecycle remains independent from gameplay state.
 */

"use client";

import * as maplibregl from "maplibre-gl";
import { type RefObject, useEffect, useRef, useState } from "react";

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
 * quizzes.
 *
 * These layers contain city, town, capital, and other place names that could
 * directly reveal quiz answers. They stay hidden regardless of the user's
 * Show Labels setting.
 */
const TOWN_QUIZ_ANSWER_LABEL_LAYER_IDS = new Set<string>([
  "Capital city labels",
  "City labels",
  "Town labels",
  "Place labels",
]);

/**
 * Parameters required to create a town quiz map.
 */
type UseTownQuizMapParams = {
  /** React-owned element in which MapLibre creates the town quiz map. */
  containerRef: RefObject<HTMLDivElement | null>;

  /** Camera position used when the country quiz first opens. */
  initialView: TownQuizInitialView;

  /**
   * Whether contextual base-map labels should remain visible.
   *
   * This affects base-map labels only. GeoPedia's custom quiz-town answer
   * labels are controlled separately by the town quiz mode.
   */
  showLabels: boolean;
};

/**
 * Values exposed to components and hooks that depend on the town quiz map.
 */
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
 * Stores the original MapTiler visibility state for each base-map symbol layer.
 *
 * MapLibre styles may intentionally contain symbol layers whose original
 * visibility is `none`. Remembering the original state allows Show Labels to
 * restore the style faithfully instead of assuming every base label should be
 * visible.
 */
type BaseLabelVisibilityMap = Map<
  string,
  maplibregl.VisibilitySpecification
>;

/**
 * Captures the original visibility of every symbol layer in the loaded base
 * map style.
 *
 * This must run only after MapLibre emits `style.load`. Before that event,
 * `getStyle()` may not yet contain a usable style object.
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
 * Answer-revealing MapTiler settlement layers remain permanently hidden.
 *
 * Every other base-map symbol layer follows the user's Show Labels setting:
 *
 * - When enabled, each layer returns to its original MapTiler visibility.
 * - When disabled, the layer is hidden.
 *
 * GeoPedia's custom town quiz labels are not part of the captured base style
 * and therefore remain unaffected by this function.
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
    /*
     * A style layer may have disappeared if the style was changed or reloaded
     * after the initial visibility snapshot.
     */
    if (!map.getLayer(layerId)) {
      continue;
    }

    /*
     * Settlement labels capable of revealing quiz answers remain hidden in
     * both Show Labels states.
     */
    if (TOWN_QUIZ_ANSWER_LABEL_LAYER_IDS.has(layerId)) {
      map.setLayoutProperty(layerId, "visibility", "none");

      continue;
    }

    /*
     * Restore each contextual layer's original MapTiler state when labels are
     * enabled rather than assuming every symbol layer should be visible.
     */
    map.setLayoutProperty(
      layerId,
      "visibility",
      showLabels ? originalVisibility : "none",
    );
  }
}

/**
 * Creates and manages the MapLibre instance used by a town quiz.
 *
 * Map creation depends only on values that fundamentally define the map.
 * Runtime Show Labels changes are handled by a separate synchronization effect
 * so toggling the setting does not destroy and recreate MapLibre.
 *
 * @param params - Town-map container, initial view, and display settings.
 * @param params.containerRef - React-owned MapLibre container.
 * @param params.initialView - Initial camera position for the country.
 * @param params.showLabels - Whether contextual base labels should be visible.
 * @returns MapLibre instance ref and readiness state.
 */
export function useTownQuizMap({
  containerRef,
  initialView,
  showLabels,
}: UseTownQuizMapParams): UseTownQuizMapResult {
  /**
   * Long-lived reference to the MapLibre instance.
   *
   * Updating the ref itself does not cause React to render.
   */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /**
   * Signals when the base MapTiler style has loaded and dependent map hooks may
   * safely add or modify layers.
   */
  const [isMapReady, setIsMapReady] = useState(false);

  /**
   * Original visibility state of every symbol layer belonging to the MapTiler
   * base style.
   *
   * Custom GeoPedia town layers are added later and are intentionally absent
   * from this snapshot.
   */
  const baseLabelVisibilityRef = useRef<BaseLabelVisibilityMap>(
    new Map(),
  );

  /**
   * Latest Show Labels value.
   *
   * The map-creation effect deliberately does not depend on `showLabels`,
   * because changing that setting must not recreate the map. The ref lets the
   * asynchronous `style.load` callback still read the latest setting.
   */
  const showLabelsRef = useRef(showLabels);

  /**
   * Keeps the mutable Show Labels ref synchronized with React state.
   */
  useEffect(() => {
    showLabelsRef.current = showLabels;
  }, [showLabels]);

  /**
   * Creates and destroys the MapLibre instance.
   *
   * This effect does not depend on `showLabels`. Display-setting changes are
   * applied to the existing map by the synchronization effect below.
   */
  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    /**
     * Preserve the visibility snapshot owned by this specific map lifecycle.
     *
     * Capturing the Map object here ensures cleanup clears the same snapshot that
     * was used by this effect even if the React ref later points somewhere else.
     */
    const baseLabelVisibility = baseLabelVisibilityRef.current;

    /*
     * Preserve the already-validated container across the asynchronous map
     * initialization boundary.
     */
    const mapContainer = container;

    let map: maplibregl.Map | null = null;

    let isCancelled = false;

    /**
     * Creates the shared town quiz map after GeoPedia prepares its MapTiler
     * style.
     */
    async function initializeMap(): Promise<void> {
      /*
       * Town quizzes always start from GeoPedia's shared MapTiler style.
       *
       * Town-specific answer-label suppression is applied after `style.load`.
       */
      const mapStyle = createMapStyle(TOWN_QUIZ_MAP_STYLE);

      /*
       * The component may have unmounted while style preparation was underway.
       */
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

      /*
       * Use a slower wheel zoom rate than MapLibre's default so country-scale
       * town maps remain easier to navigate precisely.
       */
      createdMap.scrollZoom.setWheelZoomRate(1 / 300);

      /**
       * Finalizes town-map setup once the MapTiler style exists.
       *
       * Capturing original visibility must happen before GeoPedia hides any
       * labels; otherwise the snapshot would incorrectly remember the
       * quiz-modified state as the original MapTiler state.
       */
      createdMap.on("style.load", () => {
        if (isCancelled) {
          return;
        }

        /*
         * Record the untouched MapTiler symbol-layer visibility first.
         */
        captureBaseLabelVisibility(createdMap, baseLabelVisibility);

        /*
         * Apply permanent answer-label suppression and the user's persisted
         * contextual Show Labels setting.
         */
        applyTownQuizBaseLabelVisibility(
          createdMap,
          baseLabelVisibility,
          showLabelsRef.current,
        );

        /*
         * Dependent hooks may now safely add GeoPedia town layers.
         */
        setIsMapReady(true);
      });
    }

    void initializeMap();

    return () => {
      isCancelled = true;

      setIsMapReady(false);

      baseLabelVisibility.clear();

      mapRef.current = null;

      map?.remove();
    };
  }, [containerRef, initialView]);

  /**
   * Synchronizes contextual base-map label visibility on an already-loaded map.
   *
   * Toggling Show Labels modifies MapLibre layer visibility in place and never
   * recreates the map.
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
