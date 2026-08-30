import type { QuizQuestion, QuizQuestionPrompt } from "@/types/quiz";

/**
 * Returns the presentation shown for one quiz question.
 *
 * Existing questions without an explicit prompt retain GeoPedia's historical
 * display -> answer fallback behavior.
 */
export function getQuizQuestionPrompt(
  question: QuizQuestion | undefined,
): QuizQuestionPrompt {
  if (!question) {
    return {
      type: "text",
      text: "Finished!",
    };
  }

  if (question.prompt) {
    return question?.prompt;
  }

  return {
    type: "text",
    text: question.display ?? question.answer,
  };
}
