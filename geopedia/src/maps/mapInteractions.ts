/**
 * Registers MapLibre interaction handlers for GeoPedia maps.
 *
 * This module connects MapLibre mouse and click events to GeoPedia's
 * navigation, quiz, and Show Answers behavior.
 *
 * It supports:
 *
 * - Navigation-map feature hovering and clicking
 * - Normal Mode quiz interaction
 * - Hard Mode interaction
 * - Single-answer geographic features
 * - Multi-answer geographic features such as area-code overlays
 * - Incorrect-selection feedback
 * - Show Answers feature/label hover synchronization
 *
 * React values that can change while MapLibre event handlers remain alive
 * are supplied through refs. This prevents ordinary quiz/settings changes
 * from requiring the MapLibre map to be recreated.
 */

import type * as maplibregl from "maplibre-gl";
import type React from "react";

import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

import type {
  HoverConfig,
  HoveredFeature,
  IncorrectSelection,
  MapClickBehavior,
} from "./types";

/**
 * Values required to connect MapLibre interactions with GeoPedia's React
 * state and navigation behavior.
 */
type SetupMapInteractionsParams = {
  /**
   * MapLibre map instance whose "features-fill" layer receives the event
   * handlers registered in this module.
   */
  map: maplibregl.Map;

  /**
   * Current runtime click behavior.
   *
   * This is a ref because behavior can change without recreating the map.
   * For example:
   *
   * quiz          -> "quiz"
   * Show Answers  -> "none"
   *
   * Navigation maps use "navigate".
   */
  clickBehaviorRef: React.RefObject<MapClickBehavior>;

  /**
   * Static configuration describing whether this map supports hover and
   * which feature property should be used for navigation hover labels.
   */
  hover?: HoverConfig;

  /**
   * Runtime switch controlling whether feature hover is currently enabled.
   *
   * Normal quizzes can disable hover when Borders is turned off, while
   * Show Answers can enable it again so a feature and its answer label can
   * be visually linked.
   */
  hoverEnabledRef: React.RefObject<boolean>;

  /**
   * Latest quiz definition.
   */
  quizRef: React.RefObject<Quiz | undefined>;

  /**
   * Latest quiz mode.
   *
   * Hard Mode intentionally keeps already-answered features interactive so
   * previous answers do not help the user eliminate possibilities.
   */
  quizModeRef: React.RefObject<QuizMode>;

  /**
   * Latest question currently being asked.
   */
  currentQuestionRef: React.RefObject<QuizQuestion | undefined>;

  /**
   * Function used to report whether the selected geography was correct.
   */
  answerQuestionRef: React.RefObject<(isCorrect: boolean) => void>;

  /**
   * Latest status of every completed quiz answer.
   */
  answerStatusesRef: React.RefObject<Record<string, AnswerStatus>>;

  /**
   * Controls whether a wrong click should display the temporary
   * incorrect-selection popup.
   */
  showIncorrectSelectionRef: React.RefObject<boolean>;

  /**
   * Reports the currently hovered feature ID to React.
   *
   * Show Answers uses this ID to apply hover styling to the HTML answer
   * marker belonging to the same geographic feature.
   */
  setHoveredFeatureId: (featureId: string | null) => void;

  /**
   * Updates temporary incorrect-selection feedback.
   */
  setIncorrectSelection: (selection: IncorrectSelection | null) => void;

  /**
   * Called when a navigation map feature is selected.
   */
  navigateToCountry: (countryId: string) => void;

  /**
   * Updates the floating feature label used by navigation maps.
   */
  setHoveredFeature: (feature: HoveredFeature | null) => void;
};

/**
 * Normalizes a feature's quiz value into an array of answer strings.
 *
 * Single-answer feature:
 *
 *   "MN"
 *   -> ["MN"]
 *
 * Multi-answer feature:
 *
 *   ["442", "760"]
 *   -> ["442", "760"]
 *
 * Keeping one normalized representation allows the remaining interaction
 * logic to work identically for both quiz types.
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
 * Returns a user-facing display label for the answers represented by a
 * geographic feature.
 *
 * A quiz question's display value is preferred when present. Its raw answer
 * is used as a fallback.
 *
 * Multi-answer features are joined into one readable string:
 *
 *   ["208", "986"]
 *   -> "208 / 986"
 */
function getFeatureDisplayLabel(
  featureAnswers: string[],
  quiz: Quiz,
): string {
  return featureAnswers
    .map((answer) => {
      const question = quiz.questions.find(
        (question) => question.answer === answer,
      );

      return question?.display ?? question?.answer ?? answer;
    })
    .join(" / ");
}

/**
 * Returns true when every quiz answer represented by a geographic feature
 * has already been completed.
 *
 * Both correct and wrong statuses count as completed because either means
 * the corresponding question has left the active queue.
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
 * Returns true if correctly answering currentAnswer would complete all
 * questions belonging to the geographic feature.
 *
 * This calculation happens before answerQuestion is called because React has
 * not yet updated answerStatusesRef at that point.
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
 * Registers all hover and click interactions for GeoPedia's
 * "features-fill" layer.
 */
export function setupMapInteractions({
  map,

  clickBehaviorRef,

  hover,
  hoverEnabledRef,

  quizRef,
  quizModeRef,
  currentQuestionRef,
  answerQuestionRef,
  answerStatusesRef,

  showIncorrectSelectionRef,

  setHoveredFeatureId,
  setIncorrectSelection,

  navigateToCountry,
  setHoveredFeature,
}: SetupMapInteractionsParams) {
  /**
   * Locally remembers which MapLibre feature currently has hover state.
   *
   * React does not need this value for MapLibre's own hover cleanup, so a
   * normal mutable variable is sufficient.
   */
  let hoveredFeatureId: string | null = null;

  /*
   * Only install hover handlers on maps whose configuration supports hover.
   *
   * Whether hover is currently active is checked dynamically inside the
   * handler through hoverEnabledRef.
   */
  if (hover?.enabled) {
    map.on("mousemove", "features-fill", (event) => {
      /**
       * Hover can be switched off at runtime without reinstalling event
       * handlers or rebuilding the MapLibre map.
       *
       * If hover becomes disabled while a feature is already highlighted,
       * clear both MapLibre's feature-state and React's hovered feature ID.
       */
      if (!hoverEnabledRef.current) {
        if (hoveredFeatureId !== null) {
          map.setFeatureState(
            {
              source: "features",

              id: hoveredFeatureId,
            },
            {
              hover: false,
            },
          );

          hoveredFeatureId = null;
        }

        setHoveredFeatureId(null);

        setHoveredFeature(null);

        return;
      }

      const feature = event.features?.[0];

      if (!feature) {
        return;
      }

      const featureId = feature.id;

      /*
       * GeoPedia currently promotes string IDs for interactive geographic
       * features. Features without a usable ID cannot safely use
       * feature-state or synchronize with Show Answers labels.
       */
      if (typeof featureId !== "string") {
        return;
      }

      /**
       * Remove MapLibre hover state from the previously hovered feature
       * before applying it to a different one.
       */
      if (hoveredFeatureId !== null && hoveredFeatureId !== featureId) {
        map.setFeatureState(
          {
            source: "features",

            id: hoveredFeatureId,
          },
          {
            hover: false,
          },
        );
      }

      const clickBehavior = clickBehaviorRef.current;

      /**
       * Normal Mode completed features stop being interactive.
       *
       * This prevents already-completed regions from revealing themselves
       * through hover and prevents the user from clicking them again.
       *
       * Hard Mode intentionally does NOT use this restriction. All
       * geographic features remain visually possible answers so the user
       * cannot narrow the quiz down based on previously completed regions.
       *
       * Show Answers has clickBehavior "none", so it also bypasses this
       * completed-feature restriction and allows every feature to hover.
       */
      if (clickBehavior === "quiz" && quizRef.current) {
        const featureValue =
          feature.properties?.[quizRef.current.answerProperty];

        const featureAnswers = getFeatureAnswers(featureValue);

        const isHardMode = quizModeRef.current === "hard";

        if (
          !isHardMode &&
          isFeatureFullyAnswered(featureAnswers, answerStatusesRef.current)
        ) {
          /*
           * The cursor may have entered a feature that was previously
           * hoverable but became complete after the last click.
           */
          if (hoveredFeatureId !== null) {
            map.setFeatureState(
              {
                source: "features",

                id: hoveredFeatureId,
              },
              {
                hover: false,
              },
            );

            hoveredFeatureId = null;
          }

          setHoveredFeatureId(null);

          return;
        }
      }

      hoveredFeatureId = featureId;

      /*
       * Report the hovered ID to React.
       *
       * Show Answers uses this to highlight the HTML answer marker whose
       * key matches this feature ID.
       */
      setHoveredFeatureId(featureId);

      /**
       * Apply MapLibre feature-state hover.
       *
       * The separate GeoPedia hover fill layer reads this state and darkens
       * the feature while preserving the underlying quiz/progress color.
       */
      map.setFeatureState(
        {
          source: "features",

          id: featureId,
        },
        {
          hover: true,
        },
      );

      /**
       * Navigation maps additionally display a floating name beside the
       * cursor.
       *
       * Quiz maps and Show Answers use geographic hover without this
       * floating navigation label.
       */
      if (clickBehavior === "navigate") {
        const label = feature.properties?.[hover.labelProperty];

        if (typeof label !== "string") {
          return;
        }

        setHoveredFeature({
          name: label,

          x: event.point.x,

          y: event.point.y,
        });
      }
    });

    /**
     * Remove all hover-related state when the pointer leaves GeoPedia's
     * feature layer.
     */
    map.on("mouseleave", "features-fill", () => {
      if (hoveredFeatureId !== null) {
        map.setFeatureState(
          {
            source: "features",

            id: hoveredFeatureId,
          },
          {
            hover: false,
          },
        );

        hoveredFeatureId = null;
      }

      setHoveredFeatureId(null);

      setHoveredFeature(null);
    });
  }

  /**
   * Register the feature click handler once.
   *
   * The current behavior is read from clickBehaviorRef on every click so
   * changing between quiz and Show Answers does not require this listener
   * or the MapLibre map to be recreated.
   */
  map.on("click", "features-fill", (event) => {
    const feature = event.features?.[0];

    if (!feature) {
      return;
    }

    const clickBehavior = clickBehaviorRef.current;

    /**
     * "none" is intentionally a complete no-op.
     *
     * Show Answers uses this behavior so studying the answers cannot submit
     * quiz responses.
     */
    if (clickBehavior === "none") {
      return;
    }

    /**
     * Navigation maps use the promoted feature ID as the country route ID.
     */
    if (clickBehavior === "navigate") {
      if (feature.id === undefined) {
        return;
      }

      const countryId = String(feature.id).toLowerCase();

      navigateToCountry(countryId);

      return;
    }

    /**
     * Quiz interaction requires both a current quiz definition and an
     * active question.
     */
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

      const isHardMode = quizModeRef.current === "hard";

      /**
       * Normal Mode prevents completed geographic features from being
       * selected again.
       *
       * Hard Mode deliberately leaves them clickable because allowing the
       * user to eliminate completed regions would make the quiz easier.
       */
      if (
        !isHardMode &&
        isFeatureFullyAnswered(featureAnswers, answerStatusesRef.current)
      ) {
        return;
      }

      const currentAnswer = currentQuestionRef.current.answer;

      const isCorrect = featureAnswers.includes(currentAnswer);

      /**
       * Optionally display the actual identity of an incorrectly selected
       * geographic feature.
       *
       * The popup uses display values when available and therefore works
       * with states, abbreviations, ZIP prefixes, counties, area-code
       * overlays, and future quiz types.
       */
      if (!isCorrect && showIncorrectSelectionRef.current) {
        const clickedLabel = getFeatureDisplayLabel(
          featureAnswers,
          quizRef.current,
        );

        setIncorrectSelection({
          label: clickedLabel,

          x: event.point.x,

          y: event.point.y,
        });
      }

      /**
       * Calculate whether this correct answer would complete the entire
       * geographic feature before updating React quiz state.
       *
       * answerStatusesRef still contains the pre-click values at this
       * exact moment.
       */
      const completesFeature =
        isCorrect &&
        willFeatureBeFullyAnswered(
          featureAnswers,
          currentAnswer,
          answerStatusesRef.current,
        );

      answerQuestionRef.current(isCorrect);

      /**
       * In Normal Mode, immediately remove hover when the correct click
       * completes the feature.
       *
       * Waiting for another mousemove would briefly leave a completed
       * feature highlighted.
       *
       * Hard Mode intentionally keeps completed features hoverable, so this
       * cleanup must NOT run there.
       */
      if (
        !isHardMode &&
        completesFeature &&
        typeof feature.id === "string"
      ) {
        map.setFeatureState(
          {
            source: "features",

            id: feature.id,
          },
          {
            hover: false,
          },
        );

        if (hoveredFeatureId === feature.id) {
          hoveredFeatureId = null;

          setHoveredFeatureId(null);
        }
      }
    }
  });
}
