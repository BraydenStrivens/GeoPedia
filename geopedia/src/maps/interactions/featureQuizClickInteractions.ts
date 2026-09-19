/**
 * Registers geographic feature click behavior for GeoPedia's feature quiz
 * maps.
 *
 * Supported interactions include:
 *
 * - Submitting answers during an active feature quiz.
 * - Temporarily revealing an incorrectly selected feature using the quiz's
 *   selected answer language.
 * - Temporarily revealing a selected feature for inspection while the quiz is
 *   inactive.
 * - Toggling features during manual group selection.
 * - Disabling feature clicks while Show Answers is active.
 *
 * Temporary feature-selection feedback is shared by active incorrect-answer
 * feedback and inactive feature inspection. The presentation layer determines
 * how that selection should be styled for the current quiz state.
 *
 * Country navigation is handled independently by `BaseWorldNavigationMap`.
 */

import * as maplibregl from "maplibre-gl";

import {
  FEATURE_FILL_LAYER_ID,
  FEATURE_SOURCE_ID,
} from "@/maps/constants/mapLayerIds";

import {
  getFeatureAnswerLabelContent,
  getFeatureAnswers,
  isFeatureFullyAnswered,
  willFeatureBeFullyAnswered,
} from "../labels/feature/featureAnswers";
import type {
  FeatureHoverState,
  QuizMapInteractionContext,
} from "./featureQuizInteractionTypes";

/**
 * MapLibre feature information required by GeoPedia's feature click handlers.
 */
type ClickedMapFeature = {
  /** Stable feature ID supplied by MapLibre. */
  id?: string | number;

  /** GeoJSON properties associated with the selected feature. */
  properties?: Record<string, unknown> | null;
};

/**
 * MapLibre click event produced by an event registered against a geographic
 * feature layer.
 */
type FeatureClickEvent = maplibregl.MapMouseEvent & {
  features?: maplibregl.MapGeoJSONFeature[];
};

/**
 * Extends geographic bounds with every coordinate contained in a GeoJSON
 * geometry.
 */
function extendBoundsWithCoordinates(
  bounds: maplibregl.LngLatBounds,
  coordinates: unknown,
): void {
  if (!Array.isArray(coordinates)) {
    return;
  }

  if (
    coordinates.length >= 2 &&
    typeof coordinates[0] === "number" &&
    typeof coordinates[1] === "number"
  ) {
    bounds.extend([coordinates[0], coordinates[1]]);

    return;
  }

  for (const coordinate of coordinates) {
    extendBoundsWithCoordinates(bounds, coordinate);
  }
}

/**
 * Finds the geographic feature representing the current quiz answer.
 */
function findFeatureForAnswer(
  map: maplibregl.Map,
  answerProperty: string,
  answer: string,
): maplibregl.GeoJSONFeature | null {
  const features = map.querySourceFeatures(FEATURE_SOURCE_ID);

  for (const feature of features) {
    const featureAnswers = getFeatureAnswers(
      feature.properties?.[answerProperty],
    );

    if (featureAnswers.includes(answer)) {
      return feature;
    }
  }

  return null;
}

/**
 * Returns a screen position near the top-center of a geographic feature.
 */
function getFeaturePopupPoint(
  map: maplibregl.Map,
  feature: maplibregl.GeoJSONFeature,
): maplibregl.Point | null {
  const geometry = feature.geometry;

  if (
    geometry.type !== "Polygon" &&
    geometry.type !== "MultiPolygon"
  ) {
    return null;
  }

  const bounds = new maplibregl.LngLatBounds();

  extendBoundsWithCoordinates(bounds, geometry.coordinates);

  if (bounds.isEmpty()) {
    return null;
  }

  const west = bounds.getWest();
  const east = bounds.getEast();
  const north = bounds.getNorth();

  return map.project([(west + east) / 2, north]);
}

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
 * Handles a geographic feature selection during normal feature-quiz map
 * interaction.
 *
 * While the quiz is inactive, selecting a feature acts as a lightweight study
 * interaction and temporarily reveals that feature's answer without modifying
 * quiz progress.
 *
 * During an active quiz, the selected feature may represent one or multiple
 * quiz answers. Normal Mode prevents already completed features from being
 * selected again, while Hard Mode keeps them interactive so completed
 * geography does not reveal information about unanswered questions.
 *
 * Incorrect active-quiz selections can use the same temporary feature-selection
 * state used by inactive inspection.
 *
 * @param context - Shared feature quiz map interaction dependencies.
 * @param hoverState - Mutable hover state shared with hover interactions.
 * @param feature - Geographic feature selected by the user.
 * @param pointX - Horizontal click position used by selection feedback.
 * @param pointY - Vertical click position used by selection feedback.
 */
function handleFeatureQuizSelection(
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
    questionLanguageRef,
    isQuizRunningRef,
    currentQuestionRef,
    answerQuestionRef,
    answerStatusesRef,
    showIncorrectSelectionRef,
    setFeatureSelection,
    setCorrectFeatureSelection,
    setHoveredFeatureId,
  } = context;

  const quiz = quizRef.current;

  const featureValue = feature.properties?.[quiz.answerProperty];

  const featureAnswers = getFeatureAnswers(featureValue);

  if (featureAnswers.length === 0) {
    return;
  }

  /*
   * Inactive feature quiz maps act as lightweight study maps.
   *
   * Selecting a feature temporarily reveals its answer without modifying quiz
   * progress, answer statuses, score, or current-question state.
   *
   * This interaction is available both before a quiz has started and after a
   * quiz has ended.
   *
   * The existing Show Incorrect Selection setting currently also determines
   * whether this inactive inspection feedback is displayed.
   */
  if (!isQuizRunningRef.current) {
    if (showIncorrectSelectionRef.current) {
      const selectedFeatureContent = getFeatureAnswerLabelContent(
        featureAnswers,
        quiz,
        questionLanguageRef.current,
      );

      setFeatureSelection({
        content: selectedFeatureContent,
        x: pointX,
        y: pointY,
      });
    }

    return;
  }

  const currentQuestion = currentQuestionRef.current;

  if (!currentQuestion) {
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
   * Incorrect-answer feedback identifies the selected geography when the
   * corresponding setting is enabled.
   *
   * Correct-answer feedback identifies the correct geography when the
   * corresponding setting is enabled.
   *
   * The popup uses the same feature-selection state as inactive inspection,
   * while the React presentation layer supplies incorrect-answer styling.
   */
  if (!isCorrect && showIncorrectSelectionRef.current) {
    const selectedFeatureContent = getFeatureAnswerLabelContent(
      featureAnswers,
      quiz,
      questionLanguageRef.current,
    );

    setFeatureSelection({
      content: selectedFeatureContent,
      x: pointX,
      y: pointY,
    });

    /*
     * Also identify the correct geography.
     *
     * This is especially useful for very small features whose correct-answer
     * shading may otherwise be difficult to locate on the map.
     */
    const correctFeature = findFeatureForAnswer(
      map,
      quiz.answerProperty,
      currentAnswer,
    );

    if (correctFeature) {
      const correctFeatureAnswers = getFeatureAnswers(
        correctFeature.properties?.[quiz.answerProperty],
      );

      const correctFeatureContent = getFeatureAnswerLabelContent(
        correctFeatureAnswers,
        quiz,
        questionLanguageRef.current,
      );

      const correctFeaturePoint = getFeaturePopupPoint(
        map,
        correctFeature,
      );

      if (correctFeaturePoint) {
        setCorrectFeatureSelection({
          content: correctFeatureContent,
          x: correctFeaturePoint.x,
          y: correctFeaturePoint.y,
        });
      }
    }
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
 * Registers click behavior on a feature quiz map's primary geographic feature
 * layer.
 *
 * The current click behavior determines whether a click is ignored, toggles a
 * manual-group feature, or performs normal feature-quiz interaction.
 *
 * @param context - Shared feature quiz map interaction dependencies.
 * @param hoverState - Mutable hover state shared with hover interactions.
 * @returns Cleanup function removing the registered click listener.
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
     * The only remaining supported behavior is normal feature quiz
     * interaction.
     */
    if (clickBehavior !== "quiz") {
      return;
    }

    handleFeatureQuizSelection(
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
