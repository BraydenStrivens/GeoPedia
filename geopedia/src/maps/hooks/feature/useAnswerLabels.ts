/**
 * Owns the MapLibre HTML markers used by Show Answers mode.
 *
 * The hook creates labels for visible geographic features, rebuilds them after
 * map movement, removes them when Show Answers ends, and keeps marker hover
 * styling synchronized with the hovered geographic feature.
 */

import type { Map as MapLibreMap } from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect, useRef } from "react";

import { useLatestRef } from "@/maps/hooks/useLatestRef";
import { setAnswerLabelHovered } from "@/maps/labels/feature/answerLabelElements";
import {
  clearAnswerLabels,
  updateAnswerLabels,
} from "@/maps/labels/feature/answerLabels";
import type { AnswerLabelMarkers } from "@/maps/labels/feature/answerLabelTypes";
import type { MapConfig } from "@/maps/types";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * Values required to manage Show Answers labels.
 */
type UseAnswerLabelsParams = {
  /** Current MapLibre map instance. */
  mapRef: RefObject<MapLibreMap | null>;

  /** Whether GeoPedia's geographic source and layers are ready. */
  isMapReady: boolean;

  /** Quiz whose answers should be displayed. */
  quiz?: FeatureQuiz;

  /** Map configuration controlling answer-label density. */
  mapConfig: MapConfig;

  /** Whether Show Answers is currently enabled. */
  isShowingAnswers: boolean;

  /** ID of the geographic feature currently being hovered. */
  hoveredFeatureId: string | null;
};

/**
 * Creates and synchronizes Show Answers markers for the current map.
 *
 * @param params - Map, quiz, visibility, and hover state used by the label
 * system.
 */
export function useAnswerLabels({
  mapRef,
  isMapReady,
  quiz,
  mapConfig,
  isShowingAnswers,
  hoveredFeatureId,
}: UseAnswerLabelsParams): void {
  /**
   * Collection of currently rendered answer markers keyed by feature ID.
   *
   * `globalThis.Map` avoids confusion with MapLibre's Map class or GeoPedia's
   * React Map component.
   */
  const answerLabelMarkersRef = useRef<AnswerLabelMarkers>(
    new globalThis.Map(),
  );

  /**
   * Allows the moveend handler to read the latest hovered feature without
   * reinstalling the listener whenever hover changes.
   */
  const hoveredFeatureIdRef = useLatestRef(hoveredFeatureId);

  /**
   * Creates, rebuilds, and removes Show Answers markers.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map || !quiz) {
      return;
    }

    const labelMarkers = answerLabelMarkersRef.current;

    if (!isShowingAnswers) {
      clearAnswerLabels(labelMarkers);

      return;
    }

    const loadedMap = map;

    const loadedQuiz = quiz;

    /**
     * Rebuilds labels for the current viewport and restores hover styling to
     * the newly created marker collection.
     */
    function rebuildAnswerLabels(): void {
      updateAnswerLabels(
        loadedMap,
        loadedQuiz,
        labelMarkers,
        mapConfig.answerLabels,
        mapConfig.initialView.zoom,
      );

      setAnswerLabelHovered(
        labelMarkers,
        hoveredFeatureIdRef.current,
      );
    }

    rebuildAnswerLabels();

    /*
     * moveend is intentionally used instead of move so potentially hundreds
     * of DOM markers are not rebuilt during every animation frame.
     */
    loadedMap.on("moveend", rebuildAnswerLabels);

    return () => {
      loadedMap.off("moveend", rebuildAnswerLabels);

      clearAnswerLabels(labelMarkers);
    };
  }, [
    mapRef,
    isMapReady,
    quiz,
    mapConfig.answerLabels,
    mapConfig.initialView.zoom,
    isShowingAnswers,
    hoveredFeatureIdRef,
  ]);

  /**
   * Updates marker appearance immediately when geographic hover changes.
   */
  useEffect(() => {
    if (!isShowingAnswers) {
      return;
    }

    setAnswerLabelHovered(
      answerLabelMarkersRef.current,
      hoveredFeatureId,
    );
  }, [isShowingAnswers, hoveredFeatureId]);
}
