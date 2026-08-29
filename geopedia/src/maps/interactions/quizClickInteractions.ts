/**
 * Registers geographic feature click behavior specifically for quiz maps.
 *
 * Supported behaviors are:
 *
 * - Submitting quiz answers.
 * - Toggling features during manual group selection.
 * - Disabling feature clicks while Show Answers is active.
 *
 * Country navigation is handled independently by `BaseWorldNavigationMap`.
 */

import type * as maplibregl from "maplibre-gl";

import {
  FEATURE_FILL_LAYER_ID,
  FEATURE_SOURCE_ID,
} from "@/maps/constants/mapLayerIds";

import {
  getFeatureAnswers,
  getFeatureDisplayLabel,
  isFeatureFullyAnswered,
  willFeatureBeFullyAnswered,
} from "./featureAnswers";
import type {
  FeatureHoverState,
  QuizMapInteractionContext,
} from "./quizInteractionTypes";

/**
 * MapLibre feature information required by GeoPedia's quiz click handlers.
 */
type ClickedMapFeature = {
  /** Stable feature ID supplied by MapLibre. */
  id?: string | number;

  /** GeoJSON properties associated with the selected feature. */
  properties?: Record<string, unknown> | null;
};

/**
 * MapLibre click event produced by an event registered against a geographic
 * layer.
 */
type FeatureClickEvent = maplibregl.MapMouseEvent & {
  features?: maplibregl.MapGeoJSONFeature[];
};

/**
 * Handles a manual-group feature selection.
 *
 * MapLibre feature IDs may be strings or numbers. GeoPedia normalizes manual
 * group IDs to strings so temporary selections and persisted saved groups use
 * one consistent representation.
 *
 * @param featureId - Geographic feature ID selected on the map.
 * @param onFeatureSelect - Callback that toggles the selected feature.
 */
function handleManualFeatureSelection(
  featureId: unknown,
  onFeatureSelect: (featureId: string) => void,
): void {
  if (featureId === undefined || featureId === null) {
    return;
  }

  onFeatureSelect(String(featureId));
}

/**
 * Handles a geographic selection while quiz interaction is active.
 *
 * The selected feature may represent one or multiple quiz answers. Normal Mode
 * prevents already completed features from being selected again, while Hard
 * Mode keeps them interactive so completed geography does not reveal
 * information about unanswered questions.
 *
 * @param context - Shared quiz-map interaction dependencies.
 * @param hoverState - Mutable hover state shared with hover interactions.
 * @param feature - Geographic feature selected by the user.
 * @param pointX - Horizontal click position used by incorrect-answer feedback.
 * @param pointY - Vertical click position used by incorrect-answer feedback.
 */
function handleQuizSelection(
  context: QuizMapInteractionContext,
  hoverState: FeatureHoverState,
  feature: ClickedMapFeature,
  pointX: number,
  pointY: number,
): void {
  const {
    map,
    quizRef,
    quizModeRef,
    currentQuestionRef,
    answerQuestionRef,
    answerStatusesRef,
    showIncorrectSelectionRef,
    setIncorrectSelection,
    setHoveredFeatureId,
  } = context;

  const quiz = quizRef.current;

  const currentQuestion = currentQuestionRef.current;

  if (!currentQuestion) {
    return;
  }

  const featureValue = feature.properties?.[quiz.answerProperty];

  const featureAnswers = getFeatureAnswers(featureValue);

  if (featureAnswers.length === 0) {
    return;
  }

  const isHardMode = quizModeRef.current === "hard";

  /*
   * Normal Mode prevents completed features from being selected again.
   *
   * Hard Mode intentionally keeps them clickable so completed geography does
   * not reveal information about the remaining answers.
   */
  if (
    !isHardMode &&
    isFeatureFullyAnswered(featureAnswers, answerStatusesRef.current)
  ) {
    return;
  }

  const currentAnswer = currentQuestion.answer;

  const isCorrect = featureAnswers.includes(currentAnswer);

  /*
   * Incorrect-selection feedback identifies the selected geography when that
   * setting is enabled.
   */
  if (!isCorrect && showIncorrectSelectionRef.current) {
    const selectedFeatureLabel = getFeatureDisplayLabel(
      featureAnswers,
      quiz,
    );

    setIncorrectSelection({
      label: selectedFeatureLabel,
      x: pointX,
      y: pointY,
    });
  }

  /*
   * Determine whether this correct answer completes the entire feature before
   * React updates answerStatuses.
   */
  const completesFeature =
    isCorrect &&
    willFeatureBeFullyAnswered(
      featureAnswers,
      currentAnswer,
      answerStatusesRef.current,
    );

  answerQuestionRef.current(isCorrect);

  /*
   * Normal Mode immediately removes hover when the selected answer completes
   * the final question represented by that feature.
   *
   * Hard Mode intentionally preserves hoverability.
   */
  if (
    isHardMode ||
    !completesFeature ||
    feature.id === undefined ||
    feature.id === null
  ) {
    return;
  }

  map.setFeatureState(
    {
      source: FEATURE_SOURCE_ID,
      id: feature.id,
    },
    {
      hover: false,
    },
  );

  const normalizedFeatureId = String(feature.id);

  if (hoverState.featureId === normalizedFeatureId) {
    hoverState.featureId = null;

    setHoveredFeatureId(null);
  }
}

/**
 * Registers click behavior on a quiz map's primary geographic feature layer.
 *
 * @param context - Shared quiz-map interaction dependencies.
 * @param hoverState - Mutable hover state shared with hover interactions.
 * @returns Cleanup function removing the registered listener.
 */
export function registerQuizClickInteractions(
  context: QuizMapInteractionContext,
  hoverState: FeatureHoverState,
): () => void {
  const { map, clickBehaviorRef, onFeatureSelectRef } = context;

  function handleClick(event: FeatureClickEvent): void {
    const feature = event.features?.[0];

    if (!feature) {
      return;
    }

    const clickBehavior = clickBehaviorRef.current;

    /*
     * Normal Show Answers uses `none` so selecting visible answer geography
     * cannot accidentally submit a quiz response.
     */
    if (clickBehavior === "none") {
      return;
    }

    /*
     * Manual-selection mode toggles the selected feature in the current
     * feature-group draft.
     */
    if (clickBehavior === "select") {
      handleManualFeatureSelection(
        feature.id,
        onFeatureSelectRef.current,
      );

      return;
    }

    /*
     * The only remaining supported behavior is normal quiz interaction.
     */
    if (clickBehavior !== "quiz") {
      return;
    }

    handleQuizSelection(
      context,
      hoverState,
      feature,
      event.point.x,
      event.point.y,
    );
  }

  map.on("click", FEATURE_FILL_LAYER_ID, handleClick);

  return () => {
    map.off("click", FEATURE_FILL_LAYER_ID, handleClick);
  };
}
