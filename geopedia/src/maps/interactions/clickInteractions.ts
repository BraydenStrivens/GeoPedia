/**
 * Registers geographic feature click behavior for GeoPedia maps.
 *
 * A single long-lived MapLibre click handler supports multiple interaction
 * modes:
 *
 * - Navigation maps route the selected feature to its country page.
 * - Quiz maps submit geographic answers.
 * - Manual-selection mode toggles geographic features in a draft group.
 * - Show Answers disables feature clicks entirely.
 *
 * Current behavior is read through React refs so these modes can change
 * without recreating the MapLibre instance or reinstalling event listeners.
 */

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
  MapInteractionContext,
} from "./interactionTypes";

/**
 * MapLibre feature information required by GeoPedia's click handlers.
 */
type ClickedMapFeature = {
  /** Stable feature ID supplied by MapLibre. */
  id?: string | number;

  /** GeoJSON properties associated with the selected feature. */
  properties?: Record<string, unknown> | null;
};

/**
 * Handles a navigation-map feature selection.
 *
 * Geographic IDs are normalized to lowercase strings because navigation map
 * IDs correspond to GeoPedia country route IDs.
 *
 * @param featureId - Geographic feature ID selected on the map.
 * @param navigateToCountry - Navigation callback.
 */
function handleNavigationSelection(
  featureId: unknown,
  navigateToCountry: (countryId: string) => void,
): void {
  if (featureId === undefined || featureId === null) {
    return;
  }

  const countryId = String(featureId).toLowerCase();

  navigateToCountry(countryId);
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
 * Handles a geographic selection while quiz interaction is active.
 *
 * The selected feature may represent one or multiple quiz answers. Normal Mode
 * prevents already completed features from being selected again, while Hard
 * Mode keeps them interactive so completed geography does not reveal
 * information about unanswered questions.
 *
 * @param context - Shared map interaction dependencies.
 * @param hoverState - Mutable hover state shared with hover interactions.
 * @param feature - Geographic feature selected by the user.
 * @param pointX - Horizontal click position used by incorrect-answer feedback.
 * @param pointY - Vertical click position used by incorrect-answer feedback.
 */
function handleQuizSelection(
  context: MapInteractionContext,
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

  if (!quiz || !currentQuestion) {
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

  /*
   * React-side hover identity is normalized to strings, matching the rest of
   * GeoPedia's stable feature-ID handling.
   */
  const normalizedFeatureId = String(feature.id);

  if (hoverState.featureId === normalizedFeatureId) {
    hoverState.featureId = null;

    setHoveredFeatureId(null);
  }
}

/**
 * Registers click behavior on GeoPedia's primary geographic feature layer.
 *
 * The handler is installed once for the lifetime of the MapLibre map. Current
 * interaction mode and quiz state are read through refs supplied by
 * `MapInteractionContext`.
 *
 * @param context - Shared MapLibre, React-ref, and callback dependencies.
 * @param hoverState - Mutable hover state shared with hover interactions.
 */
export function registerClickInteractions(
  context: MapInteractionContext,
  hoverState: FeatureHoverState,
): void {
  const {
    map,
    clickBehaviorRef,
    onFeatureSelectRef,
    navigateToCountry,
  } = context;

  map.on("click", FEATURE_FILL_LAYER_ID, (event) => {
    const feature = event.features?.[0];

    if (!feature) {
      return;
    }

    const clickBehavior = clickBehaviorRef.current;

    /*
     * Normal Show Answers uses "none" so selecting visible answer geography
     * cannot accidentally submit a quiz response.
     */
    if (clickBehavior === "none") {
      return;
    }

    /*
     * Navigation maps route the selected geographic feature to its country
     * page.
     */
    if (clickBehavior === "navigate") {
      handleNavigationSelection(feature.id, navigateToCountry);

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
     * Any remaining supported click behavior must be quiz interaction.
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
  });
}
