/**
 * Coordinates GeoPedia's reusable quiz map with React quiz state and
 * map-specific UI.
 *
 * This component acts as the React-level coordinator for:
 *
 * - Quiz state.
 * - Temporary quiz-map interaction state.
 * - Long-lived MapLibre interaction refs.
 * - MapLibre lifecycle creation through `useMap`.
 * - Quiz-specific click and hover interactions.
 * - Active-group feature filtering.
 * - Manual-selection highlighting.
 * - Quiz-result feature coloring.
 * - Runtime display settings.
 * - Show Answers labels.
 * - Incorrect-selection feedback.
 *
 * World-country navigation is implemented separately by
 * `BaseWorldNavigationMap`.
 */

"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import * as maplibregl from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import IncorrectSelectionPopup from "@/components/map/IncorrectSelectionPopup";
import QuizOverlay from "@/components/quiz/QuizOverlay";
import { useAnswerLabels } from "@/maps/hooks/useAnswerLabels";
import { useIncorrectSelection } from "@/maps/hooks/useIncorrectSelection";
import { useLatestRef } from "@/maps/hooks/useLatestRef";
import { useManualSelectionColors } from "@/maps/hooks/useManualSelectionColors";
import { useMap } from "@/maps/hooks/useMap";
import { useMapDisplaySettings } from "@/maps/hooks/useMapDisplaySettings";
import { useMapFeatureFilter } from "@/maps/hooks/useMapFeatureFilter";
import { useQuizFeatureColors } from "@/maps/hooks/useQuizFeatureColors";
import { useQuizMapInteractions } from "@/maps/hooks/useQuizMapInteractions";
import type { MapConfig, QuizMapClickBehavior } from "@/maps/types";
import { useQuiz } from "@/quiz/hooks/useQuiz";
import type { Quiz } from "@/types/quiz";
import type { QuizSettings } from "@/types/quizSettings";

maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

/**
 * Props required by GeoPedia's reusable quiz-map component.
 */
type QuizMapProps = {
  /** Configuration describing the geographic map to render. */
  mapConfig: MapConfig;

  /** Quiz connected to the map. */
  quiz: Quiz;

  /**
   * Feature IDs belonging to the currently active quiz group.
   *
   * `null` represents the complete unfiltered map.
   */
  activeFeatureIds?: string[] | null;

  /** Optional persisted settings belonging to the quiz. */
  quizSettings?: QuizSettings;

  /** Whether actions available before a quiz begins are temporarily unavailable. */
  areInactiveQuizActionsDisabled?: boolean;

  /** Whether the inactive quiz is currently displaying normal answer labels. */
  isShowingAnswers?: boolean;

  /**
   * Current click behavior supported by the quiz map.
   *
   * Navigation is intentionally not supported by this component.
   */
  clickBehavior: QuizMapClickBehavior;

  /**
   * Feature IDs temporarily highlighted while constructing or editing a manual
   * quiz group.
   */
  manualSelectedFeatureIds?: ReadonlySet<string>;

  /**
   * Whether quiz-answer labels should be displayed by the manual-selection
   * workflow.
   */
  showManualSelectionAnswers?: boolean;

  /** Toggles the inactive quiz's normal Show Answers view. */
  onToggleShowAnswers?: () => void;

  /**
   * Toggles a geographic feature while manually constructing or editing a quiz
   * group.
   */
  onFeatureSelect?: (featureId: string) => void;

  /** Reports whether a quiz is currently in progress. */
  onQuizRunningChange?: (isRunning: boolean) => void;
};

/** Empty feature-selection set used when manual-selection state is absent. */
const EMPTY_MANUAL_FEATURE_SELECTION: ReadonlySet<string> =
  new Set<string>();

/**
 * Default feature-selection callback used when manual selection is inactive.
 *
 * @param _featureId - Ignored geographic feature ID.
 */
function ignoreFeatureSelection(_featureId: string): void {}

/**
 * Renders a GeoPedia quiz map and connects it to quiz state and controls.
 *
 * @param props - Quiz, map configuration, display settings, and interaction
 * callbacks.
 * @returns Interactive quiz map and quiz-specific overlay UI.
 */
export default function QuizMap({
  mapConfig,
  quiz,
  quizSettings,
  areInactiveQuizActionsDisabled = false,
  isShowingAnswers = false,
  onToggleShowAnswers,
  clickBehavior,
  activeFeatureIds = null,
  onFeatureSelect,
  manualSelectedFeatureIds = EMPTY_MANUAL_FEATURE_SELECTION,
  showManualSelectionAnswers = false,
  onQuizRunningChange,
}: QuizMapProps) {
  /** DOM element into which MapLibre creates its map. */
  const mapContainerRef = useRef<HTMLDivElement>(null);

  /** Runs the quiz state machine. */
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
  } = useQuiz(quiz, {
    recycleMissedAnswers: quizSettings?.recycleMissedAnswers ?? false,
  });

  /**
   * ID of the feature currently being hovered.
   *
   * Show Answers uses this to synchronize answer labels with hovered geography.
   */
  const [hoveredFeatureId, setHoveredFeatureId] = useState<
    string | null
  >(null);

  /** Temporary incorrect-selection feedback and automatic dismissal. */
  const { incorrectSelection, setIncorrectSelection } =
    useIncorrectSelection();

  /**
   * Normal Show Answers disables geographic feature clicks.
   *
   * Manual-selection answer labels remain independent from this state.
   */
  const effectiveClickBehavior: QuizMapClickBehavior =
    isShowingAnswers ? "none" : clickBehavior;

  /**
   * Stable refs expose current React values to long-lived MapLibre handlers
   * without recreating their event listeners.
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
   * Show Answers keeps hover enabled even when Borders is disabled so the user
   * can visually associate each answer label with its geography.
   */
  const isHoverEnabled =
    (mapConfig.hover?.enabled ?? false) &&
    (isShowingAnswers || (quizSettings?.showBorders ?? true));

  const hoverEnabledRef = useLatestRef(isHoverEnabled);

  /**
   * Persisted map-display values used both during initial map creation and
   * runtime updates.
   */
  const shouldShowShading = quizSettings?.showShading ?? true;
  const shouldShowBorders = quizSettings?.showBorders ?? true;
  const shouldShowLabels = quizSettings?.showLabels ?? true;
  const showShadingRef = useLatestRef(shouldShowShading);
  const showBordersRef = useLatestRef(shouldShowBorders);
  const showLabelsRef = useLatestRef(shouldShowLabels);

  const onFeatureSelectRef = useLatestRef(
    onFeatureSelect ?? ignoreFeatureSelection,
  );

  /**
   * Reports quiz-running state to the parent so controls that could modify the
   * active question set can be blocked while a quiz is underway.
   */
  useEffect(() => {
    onQuizRunningChange?.(isActive && !isFinished);
  }, [isActive, isFinished, onQuizRunningChange]);

  /**
   * Starts a quiz after first leaving normal Show Answers mode.
   */
  function startQuiz(): void {
    if (areInactiveQuizActionsDisabled) {
      return;
    }

    if (isShowingAnswers) {
      onToggleShowAnswers?.();
    }

    restartQuiz();
  }

  /** Creates and owns the generic MapLibre instance. */
  const { mapRef, isMapReady } = useMap({
    containerRef: mapContainerRef,

    mapConfig,

    showShadingRef,
    showBordersRef,
    showLabelsRef,
  });

  /** Registers quiz-specific geographic hover and click interactions. */
  useQuizMapInteractions({
    mapRef,
    isMapReady,

    hover: mapConfig.hover,

    clickBehaviorRef,
    hoverEnabledRef,

    quizRef,
    quizModeRef,
    currentQuestionRef,
    answerStatusesRef,
    answerQuestionRef,

    onFeatureSelectRef,

    setHoveredFeatureId,
    setIncorrectSelection,

    showIncorrectSelectionRef,
  });

  /** Synchronizes temporary manual-selection highlighting. */
  useManualSelectionColors({
    mapRef,
    isMapReady,

    promoteId: mapConfig.promoteId,

    selectedFeatureIds: manualSelectedFeatureIds,
  });

  /** Synchronizes quiz-result feature coloring. */
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

  /** Synchronizes runtime label and border settings. */
  useMapDisplaySettings({
    mapRef,
    isMapReady,

    baseMapLayers: mapConfig.baseMapLayers,

    showLabels: shouldShowLabels,

    showBorders: shouldShowBorders,
  });

  /**
   * Restricts visible and interactive geographic features to the currently
   * active quiz group.
   */
  useMapFeatureFilter({
    mapRef,
    isMapReady,

    promoteId: mapConfig.promoteId,

    featureIds: activeFeatureIds,
  });

  /**
   * Answer labels may be requested by either normal Show Answers or the manual
   * feature-selection workspace.
   */
  const shouldShowAnswerLabels =
    isShowingAnswers || showManualSelectionAnswers;

  /** Creates and synchronizes quiz-answer labels. */
  useAnswerLabels({
    mapRef,
    isMapReady,

    quiz,
    mapConfig,

    isShowingAnswers: shouldShowAnswerLabels,

    hoveredFeatureId,
  });

  return (
    <div className="relative h-full w-full">
      {/* Quiz interface */}
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
        areInactiveActionsDisabled={areInactiveQuizActionsDisabled}
        onStart={startQuiz}
        onSkip={skipQuestion}
        onRestart={restartQuiz}
        onStop={stopQuiz}
        onToggleShowAnswers={() => {
          if (areInactiveQuizActionsDisabled) {
            return;
          }

          onToggleShowAnswers?.();
        }}
      />

      {/* Incorrect quiz-selection feedback */}
      <IncorrectSelectionPopup selection={incorrectSelection} />

      {/* MapLibre map container */}
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
