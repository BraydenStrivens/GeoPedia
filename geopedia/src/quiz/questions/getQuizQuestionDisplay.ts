import type {
  FeatureQuizQuestion,
  QuizQuestionLanguage,
} from "@/types/quiz";

/**
 * Resolves the user-facing text representation of a quiz question.
 *
 * English mode uses the question's default English/international display and
 * falls back to its raw answer value.
 *
 * Native mode prefers the question's native-language display, then falls back
 * to the default display and finally the raw answer value.
 *
 * Keeping this fallback behavior centralized ensures question prompts, Show
 * Answers labels, and temporary answer-feedback popups present quiz answers
 * consistently.
 *
 * @param question - Quiz question whose display text should be resolved.
 * @param questionLanguage - Language presentation selected for the quiz.
 * @returns User-facing text for the question.
 */
export function getQuizQuestionDisplay(
  question: FeatureQuizQuestion,
  questionLanguage: QuizQuestionLanguage,
): string {
  if (questionLanguage === "native") {
    return (
      question.nativeDisplay ?? question.display ?? question.answer
    );
  }

  return question.display ?? question.answer;
}
