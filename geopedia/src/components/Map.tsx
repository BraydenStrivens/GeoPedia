/**
 * Coordinates GeoPedia's reusable MapLibre map with React quiz state
 * and map-specific UI.
 *
 * This component owns the React-facing parts of the map system: it runs
 * the quiz hook, stores hover-label state, keeps MapLibre event handlers
 * synchronized with current React values, updates quiz feature colors,
 * and renders the quiz overlay and map container.
 *
 * Low-level MapLibre setup, layers, styles, and interactions are delegated
 * to reusable map utilities and hooks.
 */

"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import * as maplibregl from "maplibre-gl";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import MapHoverLabel from "@/components/MapHoverLabel";
import QuizOverlay from "@/components/QuizOverlay";
import { useLatestRef } from "@/maps/hooks/useLatestRef";
import { useMap } from "@/maps/hooks/useMap";
import {
  setBaseMapBordersVisible,
  setBaseMapLabelsVisible,
} from "@/maps/mapStyleVisibility";
import type {
  HoveredFeature,
  MapClickBehavior,
  MapConfig,
} from "@/maps/types";
import { createFeatureColorExpression } from "@/maps/useMapColors";
import { useQuiz } from "@/quiz/useQuiz";
import type { Quiz } from "@/types/quiz";
import { QuizSettings } from "@/types/quizSettings";

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
   * useQuiz manages all quiz state regardless of whether this particular
   * map currently has a quiz. Non-quiz maps receive the empty quiz.
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
   * Stores information needed to display the floating label for a hovered
   * geographic feature.
   */
  const [hoveredFeature, setHoveredFeature] =
    useState<HoveredFeature | null>(null);

  /**
   * MapLibre event handlers can remain alive across React renders.
   *
   * These refs allow those handlers to access the newest quiz state and
   * functions without forcing the MapLibre map itself to be recreated.
   */
  const quizRef = useLatestRef(quiz);
  const currentQuestionRef = useLatestRef(currentQuestion);
  const answerQuestionRef = useLatestRef(answerQuestion);
  const answerStatusesRef = useLatestRef(answerStatuses);

  const navigateToCountry = useCallback(
    (countryId: string) => {
      router.push(`/${countryId}`);
    },
    [router],
  );

  const hoverEnabled =
    (mapConfig.hover?.enabled ?? false) &&
    (quizSettings?.showBorders ?? true);

  const hoverEnabledRef = useLatestRef(hoverEnabled);

  const showShading = quizSettings?.showShading ?? true;
  const showShadingRef = useLatestRef(showShading);

  const showBorders = quizSettings?.showBorders ?? true;
  const showBordersRef = useLatestRef(showBorders);

  const showLabels = quizSettings?.showLabels ?? true;
  const showLabelsRef = useLatestRef(showLabels);

  /**
   * Creates and manages the MapLibre instance.
   *
   * useMap handles the MapLibre lifecycle, layers, interactions, controls,
   * and cleanup while returning a ref to the current MapLibre map.
   */
  const { mapRef, isMapReady } = useMap({
    containerRef: mapContainer,
    mapConfig,

    clickBehavior,
    hoverEnabledRef,

    quizRef,
    currentQuestionRef,
    answerQuestionRef,
    answerStatusesRef,

    navigateToCountry,
    setHoveredFeature,

    showShadingRef,
    showBordersRef,
    showLabelsRef,
  });

  const answerProperty = quiz?.answerProperty;
  const answerType = quiz?.answerType;

  /**
   * Updates feature colors whenever quiz answers change.
   *
   * This effect is separate from the main MapLibre lifecycle because
   * answering a question should update the map's paint expression without
   * destroying and rebuilding the entire map.
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

    const fillExpression = createFeatureColorExpression(
      answerStatuses,
      answerProperty,
      answerType,
      mapConfig.layers.fill.color,
      quizSettings?.showShading ?? true,
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
    isMapReady,
    mapRef,
  ]);

  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    const showLabels = quizSettings?.showLabels ?? true;

    setBaseMapLabelsVisible(map, showLabels);
  }, [isMapReady, quizSettings?.showLabels, mapRef]);

  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map || !map.getLayer("features-borders")) {
      return;
    }

    const showBorders = quizSettings?.showBorders ?? true;

    /*
     * GeoPedia's quiz-feature borders.
     */
    map.setLayoutProperty(
      "features-borders",
      "visibility",
      showBorders ? "visible" : "none",
    );

    /*
     * Administrative boundaries supplied by the MapTiler base style.
     */
    setBaseMapBordersVisible(map, showBorders);
  }, [isMapReady, quizSettings?.showBorders, mapRef]);

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
          onSkip={skipQuestion}
          onRestart={restartQuiz}
          onStop={stopQuiz}
        />
      )}

      <MapHoverLabel feature={hoveredFeature} />

      <div ref={mapContainer} className="h-full w-full" />
    </div>
  );
}
