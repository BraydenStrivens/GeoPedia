/**
 * Defines the core data types used by GeoPedia's quiz system.
 *
 * These types describe quiz definitions, questions, answers, and answer
 * results. They are shared across quiz configuration, quiz logic, map
 * interactions, and UI components to keep quiz data consistent throughout
 * the application.
 */

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
 * - `multiple` indicates that a feature can represent multiple answers.
 */
export type AnswerType = "single" | "multiple";

/**
 * Represents a single question that can be asked during a quiz.
 *
 * The answer corresponds to a value stored in the GeoJSON property identified
 * by the parent quiz's `answerProperty`.
 */
export interface QuizQuestion {
  /** Value that the user must identify on the map. */
  answer: string;

  /** User-facing question text. Defaults to `answer` when omitted. */
  display?: string;
}

/**
 * Defines the complete configuration and question set for a quiz.
 *
 * A quiz identifies the map it uses, the GeoJSON property containing its
 * answers, how answers relate to geographic features, and every question
 * available to the quiz.
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

  /** Determines whether a geographic feature can represent multiple answers. */
  answerType: AnswerType;

  /** Complete set of questions available to the quiz. */
  questions: QuizQuestion[];
}
