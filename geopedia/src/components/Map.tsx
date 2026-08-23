/**
 * Coordinates GeoPedia's reusable MapLibre map with React quiz state
 * and map-specific UI.
 *
 * This component owns the React-facing parts of the map system:
 *
 * - Runs and displays quiz state
 * - Stores temporary map UI state
 * - Keeps long-lived MapLibre handlers synchronized with React state
 * - Applies quiz-result coloring
 * - Applies persisted map-display settings
 * - Manages Show Answers mode and its answer-label markers
 * - Displays hover and incorrect-selection feedback
 *
 * Low-level MapLibre setup, sources, layers, styles, and event handlers are
 * delegated to reusable utilities and hooks.
 */

"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import * as maplibregl from "maplibre-gl";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import IncorrectSelectionPopup from "@/components/IncorrectSelectionPopup";
import MapHoverLabel from "@/components/MapHoverLabel";
import QuizOverlay from "@/components/QuizOverlay";
import { useLatestRef } from "@/maps/hooks/useLatestRef";
import { useMap } from "@/maps/hooks/useMap";
import type { AnswerLabelMarker } from "@/maps/mapAnswerLabels";
import {
  clearAnswerLabels,
  setAnswerLabelHovered,
  updateAnswerLabels,
} from "@/maps/mapAnswerLabels";
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
import { createFeatureColorExpression } from "@/maps/useMapColors";
import { useQuiz } from "@/quiz/useQuiz";
import type { Quiz } from "@/types/quiz";
import type { QuizSettings } from "@/types/quizSettings";

maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

type MapProps = {
  mapConfig: MapConfig;
  quiz?: Quiz;
  quizSettings?: QuizSettings;
  clickBehavior: MapClickBehavior;
};

/**
 * Empty quiz used when the map is not being used for a quiz.
 *
 * useQuiz always expects a Quiz object, so this provides harmless default
 * data for non-quiz maps such as the world navigation map.
 */
const emptyQuiz: Quiz = {
  id: "",
  name: "",
  mapId: "",
  answerProperty: "",
  answerType: "single",
  questions: [],
};

/**
 * Renders a GeoPedia map and optionally connects it to a quiz.
 */
export default function Map({
  mapConfig,
  quiz,
  quizSettings,
  clickBehavior,
}: MapProps) {
  const router = useRouter();

  /**
   * References the DOM element into which MapLibre creates its map.
   */
  const mapContainer = useRef<HTMLDivElement>(null);

  /**
   * Runs the quiz state machine.
   *
   * Recycle Missed Answers is supplied as an option because it changes how
   * wrong answers advance through the question queue.
   *
   * Non-quiz maps receive emptyQuiz so the hook can still be called
   * unconditionally.
   */
  const {
    currentQuestion,
    answerQuestion,
    skipQuestion,
    restartQuiz,
    stopQuiz,

    answerStatuses,
    lastAnsweredAnswer,

    answeredCount,
    questionCount,
    correctCount,
    wrongCount,

    isActive,
    isFinished,
  } = useQuiz(quiz ?? emptyQuiz, {
    recycleMissedAnswers: quizSettings?.recycleMissedAnswers ?? false,
  });

  /**
   * Stores information used by the floating hover label on navigation maps.
   *
   * This is separate from hoveredFeatureId because this object also contains
   * screen coordinates for positioning the floating label.
   */
  const [hoveredFeature, setHoveredFeature] =
    useState<HoveredFeature | null>(null);

  /**
   * Stores the ID of the geographic feature currently being hovered.
   *
   * Show Answers uses this ID to highlight the answer label belonging to the
   * same feature, making the relationship clear when a label is positioned
   * away from the visual center of an irregular polygon.
   */
  const [hoveredFeatureId, setHoveredFeatureId] = useState<string | null>(
    null,
  );

  /**
   * Stores temporary feedback after the user clicks an incorrect feature.
   *
   * The popup contains the actual name/display value of the feature the user
   * clicked and disappears automatically after a short delay.
   */
  const [incorrectSelection, setIncorrectSelection] =
    useState<IncorrectSelection | null>(null);

  /**
   * Determines whether the map is currently being used as an answer-study
   * view instead of as an active quiz.
   *
   * Show Answers is intentionally temporary session state rather than a
   * persisted quiz setting. Leaving the page therefore resets it.
   */
  const [isShowingAnswers, setIsShowingAnswers] = useState(false);

  /**
   * Show Answers temporarily disables geographic click behavior.
   *
   * The incoming clickBehavior still describes what the map normally does:
   *
   * quiz map       -> "quiz"
   * navigation map -> "navigate"
   *
   * Show Answers overrides that behavior with "none" without changing the
   * underlying MapConfig or recreating the map.
   */
  const effectiveClickBehavior: MapClickBehavior = isShowingAnswers
    ? "none"
    : clickBehavior;

  /**
   * Allows MapLibre's long-lived click handler to see changes between
   * "quiz", "navigate", and "none" without recreating the map.
   */
  const clickBehaviorRef = useLatestRef(effectiveClickBehavior);

  /**
   * MapLibre event handlers can remain alive across many React renders.
   *
   * These refs let those handlers read the latest React values without
   * requiring the MapLibre map instance to be destroyed and recreated every
   * time quiz state or a user setting changes.
   */
  const quizRef = useLatestRef(quiz);

  const quizModeRef = useLatestRef(quizSettings?.mode ?? "normal");

  const currentQuestionRef = useLatestRef(currentQuestion);

  const answerQuestionRef = useLatestRef(answerQuestion);

  const answerStatusesRef = useLatestRef(answerStatuses);

  const hoveredFeatureIdRef = useLatestRef(hoveredFeatureId);

  const showIncorrectSelectionRef = useLatestRef(
    quizSettings?.showIncorrectSelection ?? true,
  );

  /**
   * Stores all HTML MapLibre markers currently being used as Show Answers
   * labels.
   *
   * This must explicitly use globalThis.Map because this React component is
   * also named Map. Without globalThis, "Map" inside this function refers to
   * the React component rather than JavaScript's built-in Map collection.
   */
  const answerLabelMarkersRef = useRef<
    globalThis.Map<string, AnswerLabelMarker>
  >(new globalThis.Map<string, AnswerLabelMarker>());

  /**
   * Provides stable navigation behavior to long-lived MapLibre handlers.
   */
  const navigateToCountry = useCallback(
    (countryId: string) => {
      router.push(`/${countryId}`);
    },
    [router],
  );

  /**
   * Hover normally depends on the map supporting hover and quiz borders
   * being enabled.
   *
   * Show Answers is the exception: hover remains available even when the
   * Borders setting is disabled because hovering connects a geographic
   * feature visually to its answer label.
   */
  const hoverEnabled =
    (mapConfig.hover?.enabled ?? false) &&
    (isShowingAnswers || (quizSettings?.showBorders ?? true));

  const hoverEnabledRef = useLatestRef(hoverEnabled);

  /**
   * Refs for persisted display settings.
   *
   * useMap reads these during initial MapLibre/style creation so the map can
   * start with the correct saved appearance rather than briefly rendering
   * default settings first.
   */
  const showShading = quizSettings?.showShading ?? true;

  const showShadingRef = useLatestRef(showShading);

  const showBorders = quizSettings?.showBorders ?? true;

  const showBordersRef = useLatestRef(showBorders);

  const showLabels = quizSettings?.showLabels ?? true;

  const showLabelsRef = useLatestRef(showLabels);

  /**
   * Starting a quiz always exits Show Answers first.
   *
   * This prevents answer labels from remaining visible after the quiz begins.
   */
  const handleStartQuiz = () => {
    setIsShowingAnswers(false);

    restartQuiz();
  };

  /**
   * Creates and owns the MapLibre map instance.
   *
   * useMap handles:
   *
   * - MapLibre creation/destruction
   * - Base style loading
   * - GeoJSON source/layer installation
   * - Feature interactions
   * - Initial persisted map-display settings
   *
   * Runtime quiz state is supplied primarily through refs so normal React
   * updates do not rebuild the MapLibre instance.
   */
  const { mapRef, isMapReady } = useMap({
    containerRef: mapContainer,

    mapConfig,

    clickBehaviorRef,

    hoverEnabledRef,

    quizRef,
    quizModeRef,
    currentQuestionRef,
    answerQuestionRef,
    answerStatusesRef,

    navigateToCountry,
    setHoveredFeature,
    setIncorrectSelection,
    setHoveredFeatureId,

    showIncorrectSelectionRef,

    showShadingRef,
    showBordersRef,
    showLabelsRef,
  });

  const answerProperty = quiz?.answerProperty;

  const answerType = quiz?.answerType;

  /**
   * Updates quiz-result coloring without rebuilding the MapLibre map.
   *
   * Normal Mode:
   *   Displays the accumulated red/green result for every answered feature.
   *
   * Hard Mode:
   *   Displays only the most recently completed answer's feature while still
   *   retaining the complete answerStatuses history internally.
   *
   * Show Answers:
   *   Temporarily passes an empty answer-status object so old quiz coloring
   *   disappears while the user is studying the answer labels.
   *
   * isMapReady is included because this effect may initially run before the
   * custom GeoPedia fill layer has been created.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (
      !isMapReady ||
      !map ||
      !map.getLayer("features-fill") ||
      !answerProperty ||
      !answerType
    ) {
      return;
    }

    const visibleAnswer =
      quizSettings?.mode === "hard" ? lastAnsweredAnswer : undefined;

    const mode = quizSettings?.mode ?? "normal";

    const visibleAnswerStatuses = isShowingAnswers ? {} : answerStatuses;

    const fillExpression = createFeatureColorExpression(
      visibleAnswerStatuses,
      answerProperty,
      answerType,
      mapConfig.layers.fill.color,
      quizSettings?.showShading ?? true,
      mode,
      visibleAnswer,
    );

    map.setPaintProperty("features-fill", "fill-color", fillExpression);
  }, [
    answerStatuses,
    answerProperty,
    answerType,
    quizSettings?.mode,
    lastAnsweredAnswer,
    mapConfig.layers.fill.color,
    quizSettings?.showShading,
    isShowingAnswers,
    isMapReady,
    mapRef,
  ]);

  /**
   * Creates and manages the HTML markers used by Show Answers.
   *
   * When Show Answers turns on:
   *   - Query the geographic features currently visible in the viewport.
   *   - Deduplicate them by feature ID.
   *   - Create one HTML answer marker per visible feature.
   *
   * After panning or zooming:
   *   - moveend rebuilds the marker set for the newly visible features.
   *
   * When Show Answers turns off or this effect is cleaned up:
   *   - Every answer marker is removed from the MapLibre map.
   *
   * We intentionally use moveend rather than move so potentially hundreds of
   * DOM markers are not constantly destroyed/recreated during every frame of
   * a pan or zoom animation.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map || !quiz) {
      return;
    }

    /*
     * Capture the current marker collection once for the lifetime of this
     * effect. This keeps the cleanup tied to the same collection instance
     * that was used when the listeners were registered.
     */
    const labelMarkers = answerLabelMarkersRef.current;

    if (!isShowingAnswers) {
      clearAnswerLabels(labelMarkers);

      return;
    }

    /*
     * TypeScript now knows map is non-null because this function closes over
     * the already-narrowed constant from above.
     */
    const loadedMap = map;
    const loadedQuiz = quiz;

    function updateLabels() {
      updateAnswerLabels(
        loadedMap,
        loadedQuiz,
        labelMarkers,
        mapConfig.answerLabels,
        mapConfig.initialView.zoom,
      );

      /*
       * Reapply label hover after rebuilding the marker set.
       *
       * Panning/zooming removes and recreates the HTML markers, so the newly
       * created marker matching the currently hovered feature must receive its
       * hover styling again.
       */
      setAnswerLabelHovered(labelMarkers, hoveredFeatureIdRef.current);
    }

    updateLabels();

    loadedMap.on("moveend", updateLabels);

    return () => {
      loadedMap.off("moveend", updateLabels);

      clearAnswerLabels(labelMarkers);
    };
  }, [isMapReady, isShowingAnswers, quiz, mapRef, hoveredFeatureIdRef]);

  /**
   * Synchronizes geographic hover state with Show Answers marker styling.
   *
   * mapInteractions reports the currently hovered feature ID. The marker
   * manager then applies the hover appearance only to the label belonging to
   * that same feature.
   *
   * This is especially useful for irregular polygons whose point-on-feature
   * label position may be visually offset from the polygon's apparent center.
   */
  useEffect(() => {
    if (!isShowingAnswers) {
      return;
    }

    setAnswerLabelHovered(answerLabelMarkersRef.current, hoveredFeatureId);
  }, [isShowingAnswers, hoveredFeatureId]);

  /**
   * Applies the user's Labels setting to MapTiler/base-map symbol layers.
   *
   * This currently controls MapTiler's own place, road, water, and POI labels.
   * GeoPedia's custom label system can replace this behavior later.
   *
   * Show Answers markers are separate and are not affected by this setting.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    const shouldShowLabels = quizSettings?.showLabels ?? true;

    setBaseMapLabelsVisible(map, shouldShowLabels);
  }, [isMapReady, quizSettings?.showLabels, mapRef]);

  /**
   * Applies the user's Borders setting.
   *
   * Two separate border systems must be controlled:
   *
   * 1. "features-borders"
   *    GeoPedia's explicit line layer surrounding quiz features.
   *
   * 2. Base-map administrative boundaries
   *    Thin state/country/etc. boundaries supplied by the MapTiler style.
   *
   * Hover behavior is handled separately through hoverEnabledRef.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map || !map.getLayer("features-borders")) {
      return;
    }

    const shouldShowBorders = quizSettings?.showBorders ?? true;

    /*
     * GeoPedia quiz-feature borders.
     */
    map.setLayoutProperty(
      "features-borders",
      "visibility",
      shouldShowBorders ? "visible" : "none",
    );

    /*
     * Administrative boundaries supplied by the base-map style.
     */
    setBaseMapBordersVisible(map, shouldShowBorders);
  }, [isMapReady, quizSettings?.showBorders, mapRef]);

  /**
   * Automatically removes the incorrect-selection popup after 1.2 seconds.
   *
   * If another incorrect feature is clicked before the timer finishes,
   * React cleans up the previous timer and starts a new one for the latest
   * selection.
   */
  useEffect(() => {
    if (!incorrectSelection) {
      return;
    }

    const timeout = window.setTimeout(() => {
      setIncorrectSelection(null);
    }, 1200);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [incorrectSelection]);

  return (
    <div className="relative h-full w-full">
      {quiz && (
        <QuizOverlay
          quizName={quiz.name}
          question={
            currentQuestion?.display ??
            currentQuestion?.answer ??
            "Finished!"
          }

          answeredCount={answeredCount}
          questionCount={questionCount}
          correctCount={correctCount}
          wrongCount={wrongCount}

          isActive={isActive}
          isFinished={isFinished}
          isMapReady={isMapReady}
          isShowingAnswers={isShowingAnswers}

          onStart={handleStartQuiz}
          onSkip={skipQuestion}
          onRestart={restartQuiz}
          onStop={stopQuiz}

          onToggleShowAnswers={() => {
            setIsShowingAnswers((previous) => !previous);
          }}
        />
      )}

      <MapHoverLabel feature={hoveredFeature} />

      <IncorrectSelectionPopup selection={incorrectSelection} />

      <div ref={mapContainer} className="h-full w-full" />
    </div>
  );
}
