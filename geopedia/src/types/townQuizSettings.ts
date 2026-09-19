/**
 * Defines persisted user settings belonging specifically to town quizzes.
 *
 * Town quizzes have a fundamentally different interaction model from GeoPedia's
 * feature-selection quizzes, so their settings intentionally use a separate
 * type rather than extending `QuizSettings`.
 */

import type { QuizQuestionLanguage } from "@/types/quiz";

/**
 * Map-label mode used by a town quiz.
 *
 * - `normal` displays the active quiz-town labels.
 * - `hard` hides quiz-town labels until a result reveals the correct town.
 */
export type TownQuizMode = "normal" | "hard";

/**
 * Persisted settings controlling one town quiz.
 */
export type TownQuizSettings = {
  /** Controls visibility of custom quiz-town answer labels. */
  mode: TownQuizMode;

  /**
   * Controls whether quiz questions use English/international or native
   * settlement names.
   */
  questionLanguage: QuizQuestionLanguage;

  /**
   * Controls contextual labels supplied by the underlying base map.
   *
   * This does not control GeoPedia's custom quiz-town answer labels; those are
   * controlled by `mode`.
   */
  showLabels: boolean;
};

/**
 * Default settings used when the user has never configured a town quiz.
 */
export const DEFAULT_TOWN_QUIZ_SETTINGS: TownQuizSettings = {
  mode: "normal",
  questionLanguage: "english",
  showLabels: true,
};
