/**
 * Provides shared utilities for reading and evaluating quiz answers stored on
 * geographic map features.
 *
 * These helpers:
 *
 * - Normalize single- and multi-answer feature data.
 * - Resolve quiz questions represented by geographic features.
 * - Resolve language-aware user-facing feature labels.
 * - Build answer-label content shared by Show Answers and temporary feedback.
 * - Determine whether a geographic feature has been fully completed.
 * - Predict whether the current correct answer would complete a feature.
 */

import { getQuizQuestionDisplay } from "@/quiz/questions/getQuizQuestionDisplay";
import type {
  AnswerStatus,
  FeatureQuiz,
  QuizQuestion,
  QuizQuestionLanguage,
} from "@/types/quiz";

import { AnswerLabelContent } from "./answerLabelTypes";

/**
 * Determines whether an unknown geographic feature value is an array
 * containing only strings.
 *
 * @param value - Unknown feature property value.
 * @returns Whether the value is a string array.
 */
function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.every((item) => typeof item === "string")
  );
}

/**
 * Normalizes a geographic feature's quiz-answer value into an array.
 *
 * Single-answer strings become one-item arrays. Multi-answer string arrays are
 * returned unchanged. Missing or malformed values return an empty array.
 *
 * @param featureValue - Raw value read from the quiz's GeoJSON answer property.
 * @returns Normalized quiz answers represented by the feature.
 */
export function getFeatureAnswers(featureValue: unknown): string[] {
  if (typeof featureValue === "string") {
    return [featureValue];
  }

  if (isStringArray(featureValue)) {
    return featureValue;
  }

  return [];
}

/**
 * Returns the quiz questions represented by a geographic feature's answer
 * values.
 *
 * Answers without a corresponding quiz question are ignored. This is useful
 * for systems such as Show Answers that need access to question-specific data
 * such as display text or image prompts.
 *
 * @param featureAnswers - Answers represented by the geographic feature.
 * @param quiz - Quiz containing the corresponding questions.
 * @returns Matching quiz questions in feature-answer order.
 */
export function getFeatureQuestions(
  featureAnswers: string[],
  quiz: FeatureQuiz,
): QuizQuestion[] {
  return featureAnswers.flatMap((answer) => {
    const matchingQuestion = quiz.questions.find(
      (question) => question.answer === answer,
    );

    return matchingQuestion ? [matchingQuestion] : [];
  });
}

/**
 * Creates the user-facing quiz-answer label for a geographic feature.
 *
 * Each matching question is resolved using the quiz's selected question
 * language. Native mode prefers `nativeDisplay`, while missing native values
 * fall back through the same display -> answer behavior used by question
 * prompts.
 *
 * Multi-answer features join their represented answers using ` / `.
 *
 * @param featureAnswers - Answers represented by the geographic feature.
 * @param quiz - Quiz used to resolve question display values.
 * @param questionLanguage - Language presentation selected for the quiz.
 * @returns User-facing label for the selected feature.
 */
export function getFeatureDisplayLabel(
  featureAnswers: string[],
  quiz: FeatureQuiz,
  questionLanguage: QuizQuestionLanguage,
): string {
  return featureAnswers
    .map((answer) => {
      const matchingQuestion = quiz.questions.find(
        (question) => question.answer === answer,
      );

      return matchingQuestion
        ? getQuizQuestionDisplay(matchingQuestion, questionLanguage)
        : answer;
    })
    .join(" / ");
}

/**
 * Determines whether every quiz answer represented by a feature has already
 * been completed.
 *
 * Both correct and incorrect results count as completed answers because either
 * result means that question has already been processed by the quiz engine.
 *
 * @param featureAnswers - Answers represented by the geographic feature.
 * @param answerStatuses - Completed quiz results keyed by answer value.
 * @returns Whether every answer belonging to the feature is complete.
 */
export function isFeatureFullyAnswered(
  featureAnswers: string[],
  answerStatuses: Record<string, AnswerStatus>,
): boolean {
  if (featureAnswers.length === 0) {
    return false;
  }

  return featureAnswers.every(
    (answer) => answerStatuses[answer] !== undefined,
  );
}

/**
 * Determines whether correctly answering the current question would complete
 * every quiz answer represented by a geographic feature.
 *
 * This check occurs before React updates `answerStatuses`, so the current
 * answer is treated as completed explicitly.
 *
 * @param featureAnswers - Answers represented by the geographic feature.
 * @param currentAnswer - Answer belonging to the current quiz question.
 * @param answerStatuses - Existing completed-answer statuses.
 * @returns Whether the current answer would complete the entire feature.
 */
export function willFeatureBeFullyAnswered(
  featureAnswers: string[],
  currentAnswer: string,
  answerStatuses: Record<string, AnswerStatus>,
): boolean {
  return featureAnswers.every(
    (answer) =>
      answer === currentAnswer ||
      answerStatuses[answer] !== undefined,
  );
}

/**
 * Creates the complete user-facing answer-label content represented by a
 * geographic feature.
 *
 * Text labels use the quiz's selected question language so Show Answers and
 * temporary answer-feedback popups match the names presented by quiz
 * questions. Image-based quizzes additionally include every image belonging
 * to the feature's matching quiz questions.
 *
 * This representation is shared by Show Answers labels and temporary
 * incorrect/inactive feature-selection feedback so both displays remain
 * visually and behaviorally consistent.
 *
 * @param featureAnswers - Quiz answers represented by the geographic feature.
 * @param quiz - Quiz used to resolve display text and optional image prompts.
 * @param questionLanguage - Language presentation selected for the quiz.
 * @returns Text and images that should be shown for the feature.
 */
export function getFeatureAnswerLabelContent(
  featureAnswers: string[],
  quiz: FeatureQuiz,
  questionLanguage: QuizQuestionLanguage,
): AnswerLabelContent {
  const questions = getFeatureQuestions(featureAnswers, quiz);

  const images = questions.flatMap((question) => {
    if (question.prompt?.type !== "image") {
      return [];
    }

    return [
      {
        imageUrl: question.prompt.imageUrl,
        alt: question.prompt.alt,
      },
    ];
  });

  return {
    label: getFeatureDisplayLabel(
      featureAnswers,
      quiz,
      questionLanguage,
    ),

    images,
  };
}
