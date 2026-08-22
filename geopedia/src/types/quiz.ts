/**
 * Defines the core data types used by GeoPedia's quiz system.
 *
 * These types describe the structure of quizzes and quiz questions.
 * They are shared across quiz definitions, quiz logic, map interactions,
 * and UI components to ensure that quiz data has a consistent structure
 * throughout the application.
 */

export type AnswerStatus = "correct" | "wrong";

export type AnswerType = "single" | "multiple";

/** * Represents a single question in a quiz.
 * The `answer` is the value that the user must identify on the map.
 * What property of the GeoJSON is used to find this answer is determined
 * by the quiz's `answerProperty`.
 * The `display` is the text to display to the user during the quiz.
 * If left undefined then the `answer` will be displayed.
 */
export interface QuizQuestion {
  answer: string;
  display?: string;
}

/** Defines the complete configuration and question set for a quiz.
 * A Quiz contains the information needed to identify the quiz, determine
 * which map it uses, determine which GeoJSON property contains the answers,
 * and provide the questions that the user will be asked.
 */
export interface Quiz {
  id: string;
  name: string;

  /** ID of the map configuration used by this quiz. */
  mapId: string;

  /** Name of the GeoJSON property that contains the value used to answer
   * this quiz. For example, a state-name quiz might use "name", while a state
   * abbreviation quiz might use "abbreviation".
   */
  answerProperty: string;

  /** The number of possible correct answers for the same geometry.
   */
  answerType: AnswerType;

  /** All questions that can be asked in the quiz. */
  questions: QuizQuestion[];
}
