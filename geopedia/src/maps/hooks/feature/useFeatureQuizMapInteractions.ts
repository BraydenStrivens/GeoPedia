/**
 * Connects a ready MapLibre feature quiz map to GeoPedia's interaction system.
 *
 * The feature-map lifecycle hook owns map creation and destruction. This hook
 * owns only the long-lived click and hover listeners required by
 * `FeatureQuizMap`.
 *
 * Feature-selection feedback is shared between active and inactive quiz
 * interactions. During an active quiz, a temporary selection can identify an
 * incorrectly clicked feature. While the quiz is inactive, the same selection
 * state can temporarily reveal the answer of a feature selected for
 * inspection.
 */

"use client";

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import type { QuizMapClickBehavior } from "@/maps/interactions/featureQuizInteractionTypes";
import { setupQuizMapInteractions } from "@/maps/interactions/setupFeatureQuizMapInteractions";
import type { FeatureSelection, HoverConfig } from "@/maps/types";
import type { QuizMode } from "@/types/featureQuizSettings";
import type {
  AnswerStatus,
  FeatureQuiz,
  QuizQuestion,
} from "@/types/quiz";

/**
 * Dependencies required by `useFeatureQuizMapInteractions`.
 */
type UseFeatureQuizMapInteractionsParams = {
  /** MapLibre instance created by the feature-map lifecycle hook. */
  mapRef: RefObject<maplibregl.Map | null>;

  /** Whether GeoPedia's geographic source and layers are ready. */
  isMapReady: boolean;

  /** Static hover configuration belonging to the current map. */
  hover?: HoverConfig;

  /** Current feature quiz map click behavior. */
  clickBehaviorRef: RefObject<QuizMapClickBehavior>;

  /** Whether geographic hover is currently enabled. */
  hoverEnabledRef: RefObject<boolean>;

  /** Current feature quiz definition. */
  quizRef: RefObject<FeatureQuiz>;

  /**
   * Whether the quiz is currently accepting scored answers.
   *
   * Inactive feature quiz maps remain clickable for temporary answer-preview
   * feedback without submitting quiz responses.
   */
  isQuizRunningRef: RefObject<boolean>;

  /** Current Normal/Hard feature quiz mode. */
  quizModeRef: RefObject<QuizMode>;

  /** Current feature quiz question. */
  currentQuestionRef: RefObject<QuizQuestion | undefined>;

  /** Completed feature quiz answer statuses. */
  answerStatusesRef: RefObject<Record<string, AnswerStatus>>;

  /** Current function used to submit a feature quiz answer result. */
  answerQuestionRef: RefObject<(isCorrect: boolean) => void>;

  /** Latest manual feature-selection callback. */
  onFeatureSelectRef: RefObject<(featureId: string) => void>;

  /** Updates the geographic feature currently hovered by the quiz map. */
  setHoveredFeatureId: (featureId: string | null) => void;

  /**
   * Updates temporary feature-selection feedback.
   *
   * The selection may represent an incorrect answer during an active quiz or
   * an answer preview while inspecting the map before a quiz begins.
   */
  setFeatureSelection: (selection: FeatureSelection | null) => void;

  /**
   * Determines whether an incorrect selection made during an active quiz
   * reveals the selected feature's answer.
   *
   * This setting applies specifically to incorrect quiz feedback and is
   * separate from inactive-map feature inspection.
   */
  showIncorrectSelectionRef: RefObject<boolean>;
};

/**
 * Registers and cleans up feature quiz map interactions once the map is ready.
 *
 * Current React values are supplied through refs so the long-lived MapLibre
 * listeners can access updated quiz state and settings without being
 * recreated for each state change.
 *
 * @param params - Ready map state, runtime refs, and feature quiz callbacks.
 */
export function useFeatureQuizMapInteractions({
  mapRef,
  isMapReady,
  hover,
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
}: UseFeatureQuizMapInteractionsParams): void {
  useEffect(() => {
    const map = mapRef.current;

    if (!map || !isMapReady) {
      return;
    }

    return setupQuizMapInteractions({
      map,
      hover,
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
  }, [
    mapRef,
    isMapReady,
    hover,
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
  ]);
}
