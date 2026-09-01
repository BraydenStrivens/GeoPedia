/**
 * Connects a ready MapLibre map to GeoPedia's quiz interaction system.
 *
 * The generic `useMap` hook owns map creation and destruction. This hook owns
 * only the long-lived click and hover listeners required by `QuizMap`.
 */

"use client";

import type * as maplibregl from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import type { QuizMapClickBehavior } from "@/maps/interactions/feature/featureQuizInteractionTypes";
import { setupQuizMapInteractions } from "@/maps/interactions/feature/setupFeatureQuizMapInteractions";
import type { HoverConfig, IncorrectSelection } from "@/maps/types";
import type {
  AnswerStatus,
  FeatureQuiz,
  QuizQuestion,
} from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

/**
 * Dependencies required by `useQuizMapInteractions`.
 */
type UseFeatureQuizMapInteractionsParams = {
  /** MapLibre instance created by `useMap`. */
  mapRef: RefObject<maplibregl.Map | null>;

  /** Whether GeoPedia's geographic source and layers are ready. */
  isMapReady: boolean;

  /** Static hover configuration belonging to the current map. */
  hover?: HoverConfig;

  /** Current quiz-map click behavior. */
  clickBehaviorRef: RefObject<QuizMapClickBehavior>;

  /** Whether geographic hover is currently enabled. */
  hoverEnabledRef: RefObject<boolean>;

  /** Current quiz definition. */
  quizRef: RefObject<FeatureQuiz>;

  /**
   * Whether the quiz is currently accepting scored answers.
   *
   * Inactive quiz maps remain clickable for answer-preview feedback without
   * submitting quiz responses.
   */
  isQuizRunningRef: RefObject<boolean>;

  /** Current Normal/Hard quiz mode. */
  quizModeRef: RefObject<QuizMode>;

  /** Current quiz question. */
  currentQuestionRef: RefObject<QuizQuestion | undefined>;

  /** Completed quiz statuses. */
  answerStatusesRef: RefObject<Record<string, AnswerStatus>>;

  /** Current function used to submit a quiz answer result. */
  answerQuestionRef: RefObject<(isCorrect: boolean) => void>;

  /** Latest manual feature-selection callback. */
  onFeatureSelectRef: RefObject<(featureId: string) => void>;

  /** Updates the geographic feature currently hovered by the quiz map. */
  setHoveredFeatureId: (featureId: string | null) => void;

  /** Updates temporary incorrect-selection feedback. */
  setIncorrectSelection: (
    selection: IncorrectSelection | null,
  ) => void;

  /** Determines whether incorrect selections reveal the selected answer. */
  showIncorrectSelectionRef: RefObject<boolean>;
};

/**
 * Registers and cleans up quiz-map interactions once the map is ready.
 *
 * @param params - Ready map state, runtime refs, and quiz callbacks.
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
  setIncorrectSelection,
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
      setIncorrectSelection,
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
    setIncorrectSelection,
    showIncorrectSelectionRef,
  ]);
}
