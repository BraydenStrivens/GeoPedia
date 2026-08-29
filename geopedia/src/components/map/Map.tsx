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
 * - Active-group feature filtering.
 * - Manual-selection highlighting.
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
import { useCallback, useEffect, useRef, useState } from "react";

import IncorrectSelectionPopup from "@/components/map/IncorrectSelectionPopup";
import MapHoverLabel from "@/components/map/MapHoverLabel";
import QuizOverlay from "@/components/quiz/QuizOverlay";
import { useAnswerLabels } from "@/maps/hooks/useAnswerLabels";
import { useIncorrectSelection } from "@/maps/hooks/useIncorrectSelection";
import { useLatestRef } from "@/maps/hooks/useLatestRef";
import { useManualSelectionColors } from "@/maps/hooks/useManualSelectionColors";
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

  /**
   * Whether actions available before a quiz begins are temporarily unavailable.
   *
   * Manual feature selection currently blocks both starting a quiz and using
   * the normal Show Answers control.
   */
  areInactiveQuizActionsDisabled?: boolean;

  /** Whether the inactive quiz is currently displaying normal answer labels. */
  isShowingAnswers?: boolean;

  /** Default behavior performed when a geographic feature is clicked. */
  clickBehavior: MapClickBehavior;

  /**
   * Feature IDs temporarily highlighted while constructing or editing a
   * manual quiz group.
   */
  manualSelectedFeatureIds?: ReadonlySet<string>;

  /**
   * Whether quiz-answer labels should be displayed by the manual-selection
   * workflow.
   *
   * Unlike the normal Show Answers mode, this does not disable feature clicks.
   */
  showManualSelectionAnswers?: boolean;

  /** Toggles the inactive quiz's normal Show Answers view. */
  onToggleShowAnswers?: () => void;

  /**
   * Toggles a geographic feature while manually constructing or editing a
   * quiz group.
   */
  onFeatureSelect?: (featureId: string) => void;

  /**
   * Reports whether a quiz is currently in progress.
   *
   * A completed or stopped quiz is not considered running.
   */
  onQuizRunningChange?: (isRunning: boolean) => void;
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

/** Empty feature-selection set used by maps without manual-selection state. */
const EMPTY_MANUAL_FEATURE_SELECTION: ReadonlySet<string> =
  new Set<string>();

/**
 * Default feature-selection callback used by maps that do not support manual
 * selection.
 *
 * @param _featureId - Ignored geographic feature ID.
 */
function ignoreFeatureSelection(_featureId: string): void {}

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
  areInactiveQuizActionsDisabled = false,
  isShowingAnswers = false,
  onToggleShowAnswers,
  clickBehavior,
  activeFeatureIds = null,
  onFeatureSelect,
  manualSelectedFeatureIds = EMPTY_MANUAL_FEATURE_SELECTION,
  showManualSelectionAnswers = false,
  onQuizRunningChange,
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
   * Show Answers uses this separately from `hoveredFeature` because answer
   * label synchronization only requires stable feature identity.
   */
  const [hoveredFeatureId, setHoveredFeatureId] = useState<
    string | null
  >(null);

  /** Temporary incorrect-selection feedback and its automatic dismissal. */
  const { incorrectSelection, setIncorrectSelection } =
    useIncorrectSelection();

  /**
   * Normal Show Answers disables geographic feature clicks.
   *
   * Manual-selection answer labels are independent from this state and therefore
   * do not disable feature interaction.
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
   * Show Answers keeps hover enabled even when Borders is disabled so the user
   * can visually associate each answer label with its geography.
   */
  const isHoverEnabled =
    (mapConfig.hover?.enabled ?? false) &&
    (isShowingAnswers || (quizSettings?.showBorders ?? true));

  const hoverEnabledRef = useLatestRef(isHoverEnabled);

  /**
   * Persisted map-display values used both during initial map creation and for
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

  /** Provides stable navigation behavior to MapLibre navigation handlers. */
  const navigateToCountry = useCallback(
    (countryId: string) => {
      router.push(`/${countryId}`);
    },
    [router],
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
   *
   * The guard protects against programmatic invocation while another map
   * workflow has temporarily disabled inactive quiz actions.
   */
  function startQuiz(): void {
    if (areInactiveQuizActionsDisabled) {
      return;
    }

    /* Starting a quiz always leaves the inactive Show Answers view. */
    if (isShowingAnswers) {
      onToggleShowAnswers?.();
    }

    restartQuiz();
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
    onFeatureSelectRef,

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
   * Synchronizes temporary manual-selection highlighting.
   */
  useManualSelectionColors({
    mapRef,
    isMapReady,

    promoteId: mapConfig.promoteId,

    selectedFeatureIds: manualSelectedFeatureIds,
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
   *
   * These states remain distinct because only normal Show Answers disables map
   * clicks.
   */
  const shouldShowAnswerLabels =
    isShowingAnswers || showManualSelectionAnswers;

  /**
   * Creates and synchronizes quiz-answer labels.
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
      )}

      {/* Navigation feature hover label */}
      <MapHoverLabel feature={hoveredFeature} />

      {/* Incorrect quiz-selection feedback */}
      <IncorrectSelectionPopup selection={incorrectSelection} />

      {/* MapLibre map container */}
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
