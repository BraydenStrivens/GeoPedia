import { getQuizQuestionDisplay } from "@/quiz/questions/getQuizQuestionDisplay";
import type {
  QuizQuestion,
  QuizQuestionLanguage,
  QuizQuestionPrompt,
} from "@/types/quiz";

/**
 * Returns the presentation shown for one quiz question.
 *
 * Explicit prompts are preserved unchanged, allowing image and other
 * specialized prompts to remain independent from text-language selection.
 *
 * Questions without an explicit prompt use the shared language-aware display
 * resolver. Native mode therefore prefers `nativeDisplay`, while both language
 * modes retain the existing display and answer fallbacks.
 *
 * @param question - Current quiz question, or undefined after completion.
 * @param questionLanguage - Language presentation selected for the quiz.
 * @returns Prompt displayed by the quiz interface.
 */
export function getQuizQuestionPrompt(
  question: QuizQuestion | undefined,
  questionLanguage: QuizQuestionLanguage,
): QuizQuestionPrompt {
  if (!question) {
    return {
      type: "text",
      text: "Finished!",
    };
  }

  if (question.prompt) {
    return question.prompt;
  }

  return {
    type: "text",
    text: getQuizQuestionDisplay(question, questionLanguage),
  };
}
