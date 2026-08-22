/**
 * Registers MapLibre interaction handlers for GeoPedia maps.
 *
 * This module connects MapLibre mouse and click events to GeoPedia's
 * navigation and quiz systems.
 *
 * Quiz interaction supports both single-answer features, such as US states,
 * and multi-answer features, such as telephone area-code overlay regions.
 * Features remain hoverable and clickable only while they still contain
 * unanswered quiz questions.
 *
 * React state is accessed through refs and callbacks so MapLibre's
 * long-lived event handlers can use the latest values without requiring
 * the map itself to be recreated.
 */

import type * as maplibregl from "maplibre-gl";
import type React from "react";

import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";

import type {
  HoverConfig,
  HoveredFeature,
  MapClickBehavior,
} from "./types";

/**
 * Values required to connect MapLibre interactions with GeoPedia.
 */
type SetupMapInteractionsParams = {
  map: maplibregl.Map;

  clickBehavior: MapClickBehavior;
  hover?: HoverConfig;
  hoverEnabledRef: React.RefObject<boolean>;

  /** Latest quiz definition used by MapLibre event handlers. */
  quizRef: React.RefObject<Quiz | undefined>;

  /** Latest question currently being asked by the quiz. */
  currentQuestionRef: React.RefObject<QuizQuestion | undefined>;

  /** Records whether the user's map selection was correct. */
  answerQuestionRef: React.RefObject<(isCorrect: boolean) => void>;

  /** Latest result of every quiz question that has been attempted. */
  answerStatusesRef: React.RefObject<Record<string, AnswerStatus>>;

  /** Called when a feature on a navigation map is selected. */
  navigateToCountry: (countryId: string) => void;

  /** Updates the floating label displayed by navigation maps. */
  setHoveredFeature: (feature: HoveredFeature | null) => void;
};

/**
 * Normalizes a feature's quiz value into an array of answers.
 *
 * Single-answer features:
 *
 *   "MN" -> ["MN"]
 *
 * Multi-answer features:
 *
 *   ["442", "760"] -> ["442", "760"]
 *
 * Returning one common representation allows the rest of the interaction
 * logic to handle both feature types the same way.
 */
function getFeatureAnswers(featureValue: unknown): string[] {
  if (typeof featureValue === "string") {
    return [featureValue];
  }

  if (
    Array.isArray(featureValue) &&
    featureValue.every((value) => typeof value === "string")
  ) {
    return featureValue;
  }

  return [];
}

/**
 * Returns true when every quiz answer associated with a feature has already
 * been attempted.
 *
 * Correct and wrong answers both count as answered because either result
 * means that question should no longer make the feature interactive.
 */
function isFeatureFullyAnswered(
  featureAnswers: string[],
  answerStatuses: Record<string, AnswerStatus>,
): boolean {
  if (featureAnswers.length === 0) {
    return false;
  }

  return featureAnswers.every(
    (answer) => answerStatuses[answer] !== undefined,
  );
}

/**
 * Returns true if answering the current question will finish the feature.
 *
 * This is used immediately after a click because React has not yet updated
 * answerStatusesRef when answerQuestion is called.
 */
function willFeatureBeFullyAnswered(
  featureAnswers: string[],
  currentAnswer: string,
  answerStatuses: Record<string, AnswerStatus>,
): boolean {
  return featureAnswers.every(
    (answer) =>
      answer === currentAnswer || answerStatuses[answer] !== undefined,
  );
}

/**
 * Registers hover and click behavior for GeoPedia's geographic feature
 * layer.
 */
export function setupMapInteractions({
  map,
  clickBehavior,
  hover,
  hoverEnabledRef,
  quizRef,
  currentQuestionRef,
  answerQuestionRef,
  answerStatusesRef,
  navigateToCountry,
  setHoveredFeature,
}: SetupMapInteractionsParams) {
  /*
   * Local mutable state is sufficient here because MapLibre, rather than
   * React, only needs to remember which feature currently has hover state.
   */
  let hoveredFeatureId: string | null = null;

  if (hover?.enabled) {
    map.on("mousemove", "features-fill", (event) => {
      /*
       * Hover can be disabled at runtime without recreating the map.
       */
      if (!hoverEnabledRef.current) {
        if (hoveredFeatureId !== null) {
          map.setFeatureState(
            {
              source: "features",
              id: hoveredFeatureId,
            },
            { hover: false },
          );

          hoveredFeatureId = null;
        }

        return;
      }

      const feature = event.features?.[0];

      if (!feature) {
        return;
      }

      const featureId = feature.id;

      if (typeof featureId !== "string") {
        return;
      }

      /*
       * Remove hover state from the feature the cursor was previously
       * over before applying it to a new feature.
       */
      if (hoveredFeatureId !== null && hoveredFeatureId !== featureId) {
        map.setFeatureState(
          {
            source: "features",
            id: hoveredFeatureId,
          },
          { hover: false },
        );
      }

      /*
       * Completed quiz features are intentionally non-interactive.
       *
       * A partially answered multi-answer feature remains interactive
       * until every answer associated with that geography has been
       * attempted.
       */
      if (clickBehavior === "quiz" && quizRef.current) {
        const featureValue =
          feature.properties?.[quizRef.current.answerProperty];

        const featureAnswers = getFeatureAnswers(featureValue);

        if (
          isFeatureFullyAnswered(featureAnswers, answerStatusesRef.current)
        ) {
          if (hoveredFeatureId !== null) {
            map.setFeatureState(
              {
                source: "features",
                id: hoveredFeatureId,
              },
              { hover: false },
            );

            hoveredFeatureId = null;
          }

          return;
        }
      }

      hoveredFeatureId = featureId;

      /*
       * Hover is represented as MapLibre feature-state. The separate
       * hover layer uses this state to darken the feature without
       * replacing its underlying quiz-progress color.
       */
      map.setFeatureState(
        {
          source: "features",
          id: featureId,
        },
        { hover: true },
      );

      const label = feature.properties?.[hover.labelProperty];

      if (typeof label !== "string") {
        return;
      }

      /*
       * Navigation maps display a floating label. Quiz maps use hover
       * only as a visual indication that a feature is still selectable.
       */
      if (clickBehavior === "navigate") {
        setHoveredFeature({
          name: label,
          x: event.point.x,
          y: event.point.y,
        });
      }
    });

    map.on("mouseleave", "features-fill", () => {
      if (hoveredFeatureId !== null) {
        map.setFeatureState(
          {
            source: "features",
            id: hoveredFeatureId,
          },
          { hover: false },
        );

        hoveredFeatureId = null;
      }

      setHoveredFeature(null);
    });
  }

  map.on("click", "features-fill", (event) => {
    const feature = event.features?.[0];

    if (!feature) {
      return;
    }

    /*
     * Navigation maps use the promoted feature ID as the GeoPedia
     * country ID.
     */
    if (clickBehavior === "navigate") {
      if (feature.id === undefined) {
        return;
      }

      const countryId = String(feature.id).toLowerCase();

      navigateToCountry(countryId);

      return;
    }

    if (
      clickBehavior === "quiz" &&
      quizRef.current &&
      currentQuestionRef.current
    ) {
      const featureValue =
        feature.properties?.[quizRef.current.answerProperty];

      const featureAnswers = getFeatureAnswers(featureValue);

      if (featureAnswers.length === 0) {
        return;
      }

      /*
       * Clicking a fully answered feature does nothing. This prevents
       * completed regions from incorrectly marking the current question
       * wrong and advancing the quiz.
       */
      if (
        isFeatureFullyAnswered(featureAnswers, answerStatusesRef.current)
      ) {
        return;
      }

      const currentAnswer = currentQuestionRef.current.answer;

      const isCorrect = featureAnswers.includes(currentAnswer);

      /*
       * Determine completion before updating React state because
       * answerStatusesRef still contains the pre-click values here.
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
       * If this was the feature's final unanswered question, immediately
       * remove hover state rather than waiting for another mousemove.
       */
      if (completesFeature && typeof feature.id === "string") {
        map.setFeatureState(
          {
            source: "features",
            id: feature.id,
          },
          { hover: false },
        );

        if (hoveredFeatureId === feature.id) {
          hoveredFeatureId = null;
        }
      }
    }
  });
}
