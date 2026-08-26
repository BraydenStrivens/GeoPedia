/**
 * Defines the core data types used by GeoPedia's quiz system.
 *
 * These types describe quiz definitions, questions, answers, and answer
 * results. They are shared across quiz configuration, quiz logic, map
 * interactions, and UI components to keep quiz data consistent throughout
 * the application.
 */

import type { QuizGroupingConfig } from "@/quiz/groupings/types";

/**
 * Represents the result of a completed quiz question.
 *
 * - `correct` indicates that the correct geographic feature was selected.
 * - `wrong` indicates that an incorrect geographic feature was selected.
 */
export type AnswerStatus = "correct" | "wrong";

/**
 * Determines how many quiz answers can belong to the same geographic feature.
 *
 * - `single` indicates that each feature represents one answer.
 * - `multiple` indicates that one feature can represent multiple answers.
 */
export type AnswerType = "single" | "multiple";

/**
 * Represents one question that can be asked during a quiz.
 *
 * The answer corresponds to a value stored in the GeoJSON property identified
 * by the parent quiz's `answerProperty`.
 */
export interface QuizQuestion {
  /** Raw answer value the user must identify on the map. */
  answer: string;

  /**
   * Optional user-facing question text.
   *
   * The raw `answer` value is displayed when this is omitted.
   */
  display?: string;
}

/**
 * Defines the complete configuration and question set for a quiz.
 *
 * A quiz identifies:
 *
 * - The map it uses.
 * - The GeoJSON property containing its answers.
 * - Whether one feature may represent multiple answers.
 * - Optional property-based grouping capabilities.
 * - Every question available to the quiz.
 */
export interface Quiz {
  /** Unique identifier for the quiz. */
  id: string;

  /** User-facing name of the quiz. */
  name: string;

  /** ID of the map configuration used by this quiz. */
  mapId: string;

  /** GeoJSON property containing the feature values used as quiz answers. */
  answerProperty: string;

  /** Determines whether one geographic feature can represent multiple answers. */
  answerType: AnswerType;

  /**
   * Optional property-based grouping configuration supported by this quiz.
   *
   * Manual feature selection does not require this configuration and remains
   * available independently.
   */
  grouping?: QuizGroupingConfig;

  /** Complete set of questions available to the quiz. */
  questions: QuizQuestion[];
}
