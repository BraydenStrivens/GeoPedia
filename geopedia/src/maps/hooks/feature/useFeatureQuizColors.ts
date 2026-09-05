/**
 * Synchronizes quiz-result coloring with GeoPedia's geographic fill layer.
 *
 * Normal Mode displays accumulated results for every completed feature.
 * Hard Mode displays only the feature containing the most recently completed
 * answer. Show Answers temporarily removes quiz-result coloring entirely.
 */

import type { Map as MapLibreMap } from "maplibre-gl";
import type { RefObject } from "react";
import { useEffect } from "react";

import { createFeatureColorExpression } from "@/maps/colors/createFeatureColorExpression";
import type { MapConfig } from "@/maps/types";
import type { FeatureQuizSettings } from "@/types/featureQuizSettings";
import type { AnswerStatus, FeatureQuiz } from "@/types/quiz";

/**
 * Values required to synchronize quiz-result feature coloring.
 */
type UseFeatureQuizColorsParams = {
  /** Current MapLibre map instance. */
  mapRef: RefObject<MapLibreMap | null>;

  /** Whether GeoPedia's geographic source and layers are ready. */
  isMapReady: boolean;

  /** Feature-quiz currently associated with the map. */
  quiz?: FeatureQuiz;

  /** Map configuration supplying the normal feature color. */
  mapConfig: MapConfig;

  /** User-configurable quiz presentation settings. */
  quizSettings?: FeatureQuizSettings;

  /** Completed quiz results keyed by answer value. */
  answerStatuses: Record<string, AnswerStatus>;

  /** Most recently completed answer used by Hard Mode. */
  lastAnsweredAnswer?: string;

  /** Whether Show Answers is currently active. */
  isShowingAnswers: boolean;
};

/**
 * Keeps the map's geographic fill-color expression synchronized with current
 * quiz progress and presentation settings.
 *
 * @param params - Map, quiz, and result state used to calculate feature color.
 */
export function useFeatureQuizColors({
  mapRef,
  isMapReady,
  quiz,
  mapConfig,
  quizSettings,
  answerStatuses,
  lastAnsweredAnswer,
  isShowingAnswers,
}: UseFeatureQuizColorsParams): void {
  useEffect(() => {
    const map = mapRef.current;

    const answerProperty = quiz?.answerProperty;

    const answerType = quiz?.answerType;

    if (
      !isMapReady ||
      !map ||
      !map.getLayer("features-fill") ||
      !answerProperty ||
      !answerType
    ) {
      return;
    }

    const quizMode = quizSettings?.mode ?? "normal";

    const visibleAnswer =
      quizMode === "hard" ? lastAnsweredAnswer : undefined;

    /*
     * Show Answers is a study view rather than an active quiz display, so
     * accumulated quiz-result coloring is temporarily removed.
     */
    const visibleAnswerStatuses = isShowingAnswers
      ? {}
      : answerStatuses;

    const fillColorExpression = createFeatureColorExpression(
      visibleAnswerStatuses,
      answerProperty,
      answerType,
      mapConfig.layers.fill.color,
      quizSettings?.showShading ?? true,
      quizMode,
      visibleAnswer,
    );

    map.setPaintProperty(
      "features-fill",
      "fill-color",
      fillColorExpression,
    );
  }, [
    mapRef,
    isMapReady,
    quiz?.answerProperty,
    quiz?.answerType,
    mapConfig.layers.fill.color,
    quizSettings?.mode,
    quizSettings?.showShading,
    answerStatuses,
    lastAnsweredAnswer,
    isShowingAnswers,
  ]);
}
