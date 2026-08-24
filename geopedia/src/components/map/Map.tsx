/**
 * Coordinates GeoPedia's reusable MapLibre map with React quiz state and
 * map-specific UI.
 *
 * This component acts as the React-level coordinator for:
 *
 * - Quiz state.
 * - Temporary map interaction state.
 * - Long-lived MapLibre interaction refs.
 * - MapLibre lifecycle creation through `useMap`.
 * - Quiz-result feature coloring.
 * - Runtime display settings.
 * - Show Answers labels.
 * - Hover and incorrect-selection feedback.
 *
 * Lower-level MapLibre behavior is delegated to focused hooks and utilities.
 */

"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import * as maplibregl from "maplibre-gl";
import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";

import IncorrectSelectionPopup from "@/components/map/IncorrectSelectionPopup";
import MapHoverLabel from "@/components/map/MapHoverLabel";
import QuizOverlay from "@/components/quiz/QuizOverlay";
import { useAnswerLabels } from "@/maps/hooks/useAnswerLabels";
import { useIncorrectSelection } from "@/maps/hooks/useIncorrectSelection";
import { useLatestRef } from "@/maps/hooks/useLatestRef";
import { useMap } from "@/maps/hooks/useMap";
import { useMapDisplaySettings } from "@/maps/hooks/useMapDisplaySettings";
import { useMapFeatureFilter } from "@/maps/hooks/useMapFeatureFilter";
import { useQuizFeatureColors } from "@/maps/hooks/useQuizFeatureColors";
import type {
  HoveredFeature,
  MapClickBehavior,
  MapConfig,
} from "@/maps/types";
import { useQuiz } from "@/quiz/hooks/useQuiz";
import type { Quiz } from "@/types/quiz";
import type { QuizSettings } from "@/types/quizSettings";

maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

/**
 * Props required by GeoPedia's reusable map component.
 */
type MapProps = {
  /** Configuration describing the geographic map to render. */
  mapConfig: MapConfig;

  /** Optional quiz connected to the map. */
  quiz?: Quiz;

  /**
   * Feature IDs belonging to the currently active quiz group.
   *
   * `null` represents the complete unfiltered map.
   */
  activeFeatureIds?: string[] | null;

  /** Optional persisted settings belonging to the quiz. */
  quizSettings?: QuizSettings;

  /** Default behavior performed when a geographic feature is clicked. */
  clickBehavior: MapClickBehavior;
};

/**
 * Empty quiz supplied to `useQuiz` when the map is not being used for a quiz.
 *
 * Hooks must be called unconditionally, so navigation-only maps receive this
 * harmless definition rather than conditionally skipping `useQuiz`.
 */
const EMPTY_QUIZ: Quiz = {
  id: "",
  name: "",
  mapId: "",
  answerProperty: "",
  answerType: "single",
  questions: [],
};

/**
 * Renders a GeoPedia MapLibre map and optionally connects it to a quiz.
 *
 * @param props - Map configuration and optional quiz behavior.
 * @returns The interactive map and any map-specific overlay UI.
 */
export default function Map({
  mapConfig,
  quiz,
  quizSettings,
  clickBehavior,
  activeFeatureIds = null,
}: MapProps) {
  const router = useRouter();

  /** DOM element into which MapLibre creates its map. */
  const mapContainerRef = useRef<HTMLDivElement>(null);

  /**
   * Runs the quiz state machine.
   *
   * Navigation-only maps use EMPTY_QUIZ so the hook remains unconditional.
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
  } = useQuiz(quiz ?? EMPTY_QUIZ, {
    recycleMissedAnswers: quizSettings?.recycleMissedAnswers ?? false,
  });

  /** Feature information displayed by the floating navigation hover label. */
  const [hoveredFeature, setHoveredFeature] =
    useState<HoveredFeature | null>(null);

  /**
   * ID of the feature currently being hovered.
   *
   * Show Answers uses this separately from hoveredFeature because answer-label
   * synchronization only requires stable feature identity.
   */
  const [hoveredFeatureId, setHoveredFeatureId] = useState<
    string | null
  >(null);

  /** Temporary incorrect-selection feedback and its automatic dismissal. */
  const { incorrectSelection, setIncorrectSelection } =
    useIncorrectSelection();

  /**
   * Determines whether the inactive quiz is currently displaying its answers.
   *
   * Show Answers is temporary UI state and is intentionally not persisted.
   */
  const [isShowingAnswers, setIsShowingAnswers] = useState(false);

  /**
   * Show Answers disables feature clicking without changing the map's normal
   * configured behavior.
   */
  const effectiveClickBehavior: MapClickBehavior = isShowingAnswers
    ? "none"
    : clickBehavior;

  /**
   * Stable refs expose current React values to long-lived MapLibre handlers
   * without recreating the map or its event listeners.
   */
  const clickBehaviorRef = useLatestRef(effectiveClickBehavior);

  const quizRef = useLatestRef(quiz);

  const quizModeRef = useLatestRef(quizSettings?.mode ?? "normal");

  const currentQuestionRef = useLatestRef(currentQuestion);

  const answerQuestionRef = useLatestRef(answerQuestion);

  const answerStatusesRef = useLatestRef(answerStatuses);

  const showIncorrectSelectionRef = useLatestRef(
    quizSettings?.showIncorrectSelection ?? true,
  );

  /**
   * Show Answers keeps hover enabled even when Borders is disabled so the
   * user can visually associate each answer label with its geography.
   */
  const isHoverEnabled =
    (mapConfig.hover?.enabled ?? false) &&
    (isShowingAnswers || (quizSettings?.showBorders ?? true));

  const hoverEnabledRef = useLatestRef(isHoverEnabled);

  /**
   * Persisted map-display values used both during initial map creation and
   * for runtime updates.
   */
  const shouldShowShading = quizSettings?.showShading ?? true;

  const shouldShowBorders = quizSettings?.showBorders ?? true;

  const shouldShowLabels = quizSettings?.showLabels ?? true;

  const showShadingRef = useLatestRef(shouldShowShading);

  const showBordersRef = useLatestRef(shouldShowBorders);

  const showLabelsRef = useLatestRef(shouldShowLabels);

  /** Provides stable navigation behavior to MapLibre navigation handlers. */
  const navigateToCountry = useCallback(
    (countryId: string) => {
      router.push(`/${countryId}`);
    },
    [router],
  );

  /**
   * Starts a quiz after first leaving Show Answers mode.
   */
  function startQuiz(): void {
    setIsShowingAnswers(false);

    restartQuiz();
  }

  /**
   * Toggles Show Answers while the quiz is inactive.
   */
  function toggleShowAnswers(): void {
    setIsShowingAnswers((wasShowingAnswers) => !wasShowingAnswers);
  }

  /**
   * Creates and owns the MapLibre instance.
   */
  const { mapRef, isMapReady } = useMap({
    containerRef: mapContainerRef,

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
  });

  /**
   * Synchronizes quiz-result feature coloring.
   */
  useQuizFeatureColors({
    mapRef,
    isMapReady,
    quiz,
    mapConfig,
    quizSettings,
    answerStatuses,
    lastAnsweredAnswer,
    isShowingAnswers,
  });

  /**
   * Synchronizes runtime label and border settings.
   */
  useMapDisplaySettings({
    mapRef,
    isMapReady,
    showLabels: shouldShowLabels,
    showBorders: shouldShowBorders,
  });

  /**
   * Restricts the visible and interactive geographic features to the active
   * quiz group.
   */
  useMapFeatureFilter({
    mapRef,
    isMapReady,
    promoteId: mapConfig.promoteId,
    featureIds: activeFeatureIds,
  });

  /**
   * Creates and synchronizes Show Answers markers.
   */
  useAnswerLabels({
    mapRef,
    isMapReady,
    quiz,
    mapConfig,
    isShowingAnswers,
    hoveredFeatureId,
  });

  return (
    <div className="relative h-full w-full">
      {/* Quiz interface */}
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
          onStart={startQuiz}
          onSkip={skipQuestion}
          onRestart={restartQuiz}
          onStop={stopQuiz}
          onToggleShowAnswers={toggleShowAnswers}
        />
      )}

      {/* Navigation feature hover label */}
      <MapHoverLabel feature={hoveredFeature} />

      {/* Incorrect quiz selection feedback */}
      <IncorrectSelectionPopup selection={incorrectSelection} />

      {/* MapLibre map container */}
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
