/**
 * Determines how a quiz presents and handles its questions.
 */
export type QuizMode = "normal" | "hard" | "show-answers";

/**
 * User-configurable settings for an individual quiz.
 *
 * Settings are stored separately for each quiz so different quizzes can
 * retain their own configuration.
 */
export type QuizSettings = {
  mode: QuizMode;

  recycleMissedAnswers: boolean;

  showShading: boolean;
  showBorders: boolean;
  showLabels: boolean;

  showIncorrectSelection: boolean;
};

/**
 * Settings used when a quiz has no previously saved configuration.
 */
export const defaultQuizSettings: QuizSettings = {
  mode: "normal",

  recycleMissedAnswers: false,

  showShading: true,
  showBorders: true,
  showLabels: true,

  showIncorrectSelection: true,
};
