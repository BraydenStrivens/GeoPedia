export type QuizMode = "normal" | "hard" | "show-answers";

export type QuizSettings = {
  mode: QuizMode;

  recycleMissedAnswers: boolean;

  showShading: boolean;
  showBorders: boolean;
  showBaseMapLabels: boolean;
  showIncorrectSelection: boolean;
};

export const defaultQuizSettings: QuizSettings = {
  mode: "normal",

  recycleMissedAnswers: false,

  showShading: true,
  showBorders: true,
  showBaseMapLabels: true,
  showIncorrectSelection: true,
};
