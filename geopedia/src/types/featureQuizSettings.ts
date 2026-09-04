/**
 * Defines the persistent user-configurable settings for an individual quiz.
 *
 * Each quiz stores its own settings independently so changing the behavior
 * or appearance of one quiz does not affect other quizzes.
 *
 * These settings are intended to persist between sessions, typically through
 * localStorage.
 */

/**
 * Determines how quiz answers are visually presented during an active quiz.
 *
 * - `normal`
 *   Displays the accumulated result coloring for all answered features.
 *
 * - `hard`
 *   Displays result coloring only for the most recently completed answer
 *   while keeping all previously answered features interactive.
 */
export type QuizMode = "normal" | "hard";

/**
 * User-configurable behavior and display settings for a single quiz.
 * */
export type FeatureQuizSettings = {
  /** Determines how completed answers are visually represented during the quiz. */
  mode: QuizMode;

  /**
   * Determines whether incorrectly answered questions are returned to the end
   * of the question queue instead of being marked complete.
   *
   * When enabled, an incorrect answer still increments the wrong-answer count,
   * but the question remains unanswered and can appear again later.
   */
  recycleMissedAnswers: boolean;

  /**
   * Determines whether unanswered quiz features use the map's normal fill
   * shading.
   *
   * Quiz-result coloring can still appear independently of this setting.
   */
  showShading: boolean;

  /**
   * Determines whether quiz-feature borders and relevant base-map
   * administrative boundaries are visible.
   *
   * In Normal Mode, disabling borders also disables the standard feature
   * hover effect so hovering cannot reveal hidden region boundaries.
   */
  showBorders: boolean;

  /**
   * Determines whether labels supplied by the current base-map style are
   * visible.
   *
   * This currently controls MapTiler/base-map labels and is separate from
   * GeoPedia's Show Answers labels.
   */
  showLabels: boolean;

  /**
   * Determines whether selecting an incorrect geographic feature temporarily
   * displays that feature's actual answer near the cursor.
   */
  showIncorrectSelection: boolean;
};

/**
 * Settings used when a quiz has no previously saved configuration.
 */
export const DEFAULT_FEATURE_QUIZ_SETTINGS: FeatureQuizSettings = {
  mode: "normal",

  recycleMissedAnswers: false,

  showShading: true,
  showBorders: true,
  showLabels: true,

  showIncorrectSelection: true,
};
