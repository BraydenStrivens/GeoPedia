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

import type { QuizMapClickBehavior } from "@/maps/interactions/quizInteractionTypes";
import { setupQuizMapInteractions } from "@/maps/interactions/setupQuizMapInteractions";
import type { HoverConfig, IncorrectSelection } from "@/maps/types";
import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

/**
 * Dependencies required by `useQuizMapInteractions`.
 */
type UseQuizMapInteractionsParams = {
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
  quizRef: RefObject<Quiz>;

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
export function useQuizMapInteractions({
  mapRef,
  isMapReady,
  hover,
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
}: UseQuizMapInteractionsParams): void {
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
