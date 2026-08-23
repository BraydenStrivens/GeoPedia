/**
 * Registers geographic feature click behavior for navigation maps and quizzes.
 *
 * Click behavior is read through a React ref so a map can change between
 * interactive quiz mode and non-interactive Show Answers mode without
 * recreating its MapLibre instance.
 */

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
 * Handles a navigation-map feature selection.
 *
 * @param featureId - Promoted geographic feature ID.
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
 * Registers click behavior on GeoPedia's feature layer.
 *
 * @param context - Shared map interaction dependencies.
 * @param hoverState - Mutable hover state shared with hover interactions.
 */
export function registerClickInteractions(
  context: MapInteractionContext,
  hoverState: FeatureHoverState,
): void {
  const {
    map,
    clickBehaviorRef,
    quizRef,
    quizModeRef,
    currentQuestionRef,
    answerQuestionRef,
    answerStatusesRef,
    showIncorrectSelectionRef,
    setIncorrectSelection,
    setHoveredFeatureId,
    navigateToCountry,
  } = context;

  map.on("click", "features-fill", (event) => {
    const feature = event.features?.[0];

    if (!feature) {
      return;
    }

    const clickBehavior = clickBehaviorRef.current;

    /*
     * Show Answers uses "none" so clicking a visible answer cannot submit a
     * quiz response.
     */
    if (clickBehavior === "none") {
      return;
    }

    if (clickBehavior === "navigate") {
      handleNavigationSelection(feature.id, navigateToCountry);

      return;
    }

    const quiz = quizRef.current;

    const currentQuestion = currentQuestionRef.current;

    if (clickBehavior !== "quiz" || !quiz || !currentQuestion) {
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
     * Hard Mode keeps them clickable so previously completed regions do not
     * reveal information about the remaining answers.
     */
    if (
      !isHardMode &&
      isFeatureFullyAnswered(
        featureAnswers,
        answerStatusesRef.current,
      )
    ) {
      return;
    }

    const currentAnswer = currentQuestion.answer;

    const isCorrect = featureAnswers.includes(currentAnswer);

    if (!isCorrect && showIncorrectSelectionRef.current) {
      const selectedFeatureLabel = getFeatureDisplayLabel(
        featureAnswers,
        quiz,
      );

      setIncorrectSelection({
        label: selectedFeatureLabel,
        x: event.point.x,
        y: event.point.y,
      });
    }

    /*
     * Determine whether this answer completes the feature before React
     * updates answerStatuses.
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
     * Normal Mode immediately removes hover when the final question
     * belonging to a feature is completed.
     *
     * Hard Mode intentionally preserves hoverability.
     */
    if (
      isHardMode ||
      !completesFeature ||
      typeof feature.id !== "string"
    ) {
      return;
    }

    map.setFeatureState(
      {
        source: "features",
        id: feature.id,
      },
      {
        hover: false,
      },
    );

    if (hoverState.featureId === feature.id) {
      hoverState.featureId = null;

      setHoveredFeatureId(null);
    }
  });
}
