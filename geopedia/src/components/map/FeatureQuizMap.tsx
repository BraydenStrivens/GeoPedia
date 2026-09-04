/**
 * Coordinates GeoPedia's reusable feature quiz map with React quiz state and
 * map-specific UI.
 *
 * This component acts as the React-level coordinator for:
 *
 * - Feature quiz state.
 * - Temporary feature-map interaction state.
 * - Long-lived MapLibre interaction refs.
 * - MapLibre lifecycle creation through `useFeatureQuizMap`.
 * - Feature quiz click and hover interactions.
 * - Active-group feature filtering.
 * - Manual-selection highlighting.
 * - Quiz-result feature coloring.
 * - Runtime display settings.
 * - Show Answers labels.
 * - Temporary feature-selection feedback.
 *
 * Temporary feature-selection feedback is shared by two interactions:
 *
 * - During an active quiz, it can identify an incorrectly selected feature.
 * - While the quiz is inactive, it can temporarily reveal the selected
 *   feature's answer for inspection.
 *
 * World-country navigation is implemented separately by
 * `BaseWorldNavigationMap`.
 */

"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import * as maplibregl from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import FeatureQuizOverlay from "@/components/quiz/overlay/FeatureQuizOverlay";
import { useAnswerLabels } from "@/maps/hooks/feature/useAnswerLabels";
import { useFeatureQuizColors } from "@/maps/hooks/feature/useFeatureQuizColors";
import { useFeatureQuizMap } from "@/maps/hooks/feature/useFeatureQuizMap";
import { useFeatureQuizMapInteractions } from "@/maps/hooks/feature/useFeatureQuizMapInteractions";
import { useFeatureSelection } from "@/maps/hooks/feature/useFeatureSelection";
import { useManualSelectionColors } from "@/maps/hooks/feature/useManualSelectionColors";
import { useMapFeatureFilter } from "@/maps/hooks/feature/useMapFeatureFilter";
import { useLatestRef } from "@/maps/hooks/useLatestRef";
import { useMapDisplaySettings } from "@/maps/hooks/useMapDisplaySettings";
import type { MapConfig, QuizMapClickBehavior } from "@/maps/types";
import { useQuiz } from "@/quiz/hooks/useFeatureQuiz";
import { getQuizQuestionPrompt } from "@/quiz/questions/getQuizQuestionPrompt";
import type { FeatureQuizSettings } from "@/types/featureQuizSettings";
import type { FeatureQuiz } from "@/types/quiz";

import FeatureSelectionPopup from "./FeatureSelectionPopup";

maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

/**
 * Props required by GeoPedia's reusable feature quiz map component.
 */
type FeatureQuizMapProps = {
  /** Configuration describing the geographic map to render. */
  mapConfig: MapConfig;

  /** Feature-based quiz controlled by the map. */
  quiz: FeatureQuiz;

  /**
   * Feature IDs belonging to the currently active quiz group.
   *
   * `null` represents the complete unfiltered map.
   */
  activeFeatureIds?: string[] | null;

  /** Optional persisted settings belonging to the feature quiz. */
  quizSettings?: FeatureQuizSettings;

  /**
   * Whether actions available before a quiz begins are temporarily unavailable.
   */
  areInactiveQuizActionsDisabled?: boolean;

  /** Whether the inactive feature quiz is displaying normal answer labels. */
  isShowingAnswers?: boolean;

  /**
   * Current click behavior supported by the feature quiz map.
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

  /** Toggles the inactive feature quiz's normal Show Answers view. */
  onToggleShowAnswers?: () => void;

  /**
   * Toggles a geographic feature while manually constructing or editing a quiz
   * group.
   */
  onFeatureSelect?: (featureId: string) => void;

  /** Reports whether a feature quiz is currently in progress. */
  onQuizRunningChange?: (isRunning: boolean) => void;
};

/**
 * Empty feature-selection set used when manual-selection state is absent.
 */
const EMPTY_MANUAL_FEATURE_SELECTION: ReadonlySet<string> =
  new Set<string>();

/**
 * Default feature-selection callback used when manual selection is inactive.
 *
 * @param _featureId - Ignored geographic feature ID.
 */
function ignoreFeatureSelection(_featureId: string): void {}

/**
 * Renders a GeoPedia feature quiz map and connects it to quiz state, map
 * interactions, display settings, and quiz controls.
 *
 * @param props - Quiz, map configuration, display settings, and interaction
 * callbacks.
 * @returns Interactive feature quiz map and quiz-specific overlay UI.
 */
export default function FeatureQuizMap({
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
}: FeatureQuizMapProps) {
  /** DOM element into which MapLibre creates the feature quiz map. */
  const mapContainerRef = useRef<HTMLDivElement>(null);

  /** Runs the feature quiz state machine. */
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

  /**
   * Temporary feedback for the feature most recently selected on the map.
   *
   * During an active quiz, this may represent an incorrectly selected feature.
   * While the quiz is inactive, it represents a feature selected for temporary
   * answer inspection.
   */
  const { featureSelection, setFeatureSelection } =
    useFeatureSelection();

  /**
   * Normal Show Answers disables geographic feature clicks.
   *
   * Manual-selection answer labels remain independent from this state.
   */
  const effectiveClickBehavior: QuizMapClickBehavior =
    isShowingAnswers ? "none" : clickBehavior;

  const questionPrompt = getQuizQuestionPrompt(currentQuestion);

  const isQuizRunning = isActive && !isFinished;

  /**
   * Stable refs expose current React values to long-lived MapLibre handlers
   * without recreating their event listeners.
   */
  const isQuizRunningRef = useLatestRef(isQuizRunning);
  const clickBehaviorRef = useLatestRef(effectiveClickBehavior);
  const quizRef = useLatestRef(quiz);
  const quizModeRef = useLatestRef(quizSettings?.mode ?? "normal");
  const currentQuestionRef = useLatestRef(currentQuestion);
  const answerQuestionRef = useLatestRef(answerQuestion);
  const answerStatusesRef = useLatestRef(answerStatuses);

  /**
   * Controls whether incorrect active-quiz selections reveal the selected
   * feature's answer.
   *
   * The interaction system currently also uses this setting to determine
   * whether inactive feature inspection feedback is shown.
   */
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
   * Starts a feature quiz after first leaving normal Show Answers mode.
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

  /**
   * Creates and owns the MapLibre instance used by the feature quiz.
   */
  const { mapRef, isMapReady } = useFeatureQuizMap({
    containerRef: mapContainerRef,

    mapConfig,

    showShadingRef,
    showBordersRef,
    showLabelsRef,
  });

  /**
   * Registers feature-quiz geographic hover and click interactions.
   */
  useFeatureQuizMapInteractions({
    mapRef,
    isMapReady,

    hover: mapConfig.hover,

    clickBehaviorRef,
    hoverEnabledRef,

    quizRef,
    isQuizRunningRef,
    quizModeRef,
    currentQuestionRef,
    answerStatusesRef,
    answerQuestionRef,

    onFeatureSelectRef,

    setHoveredFeatureId,
    setFeatureSelection,

    showIncorrectSelectionRef,
  });

  /**
   * Synchronizes temporary manual-selection highlighting.
   */
  useManualSelectionColors({
    mapRef,
    isMapReady,

    promoteId: mapConfig.promoteId,

    selectedFeatureIds: manualSelectedFeatureIds,
  });

  /**
   * Synchronizes feature coloring produced by quiz results and current quiz
   * state.
   */
  useFeatureQuizColors({
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
   * Synchronizes runtime base-map label and feature-border settings.
   */
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

  /**
   * Creates and synchronizes feature quiz answer labels.
   */
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
      {/* Feature quiz interface */}
      <FeatureQuizOverlay
        quizName={quiz.name}
        question={questionPrompt}
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

      {/*
        Temporary feature-selection feedback.

        During an active quiz, displays the incorrectly selected feature using
        error styling. While the quiz is inactive, allows features to be
        inspected by temporarily displaying their answer using the default
        neutral styling.
      */}
      <FeatureSelectionPopup
        selection={featureSelection}
        backgroundClassName={isActive ? "bg-red-500" : undefined}
        textClassName={isActive ? "text-white" : undefined}
      />

      {/* MapLibre feature quiz map container */}
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
