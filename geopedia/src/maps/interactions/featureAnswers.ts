/**
 * Provides shared utilities for reading and evaluating quiz answers stored
 * on geographic features.
 *
 * These helpers normalize single- and multi-answer feature data, generate
 * user-facing labels, and determine whether geographic features have been
 * fully completed during a quiz.
 */

import type { AnswerStatus, Quiz } from "@/types/quiz";

/**
 * Normalizes a geographic feature's quiz value into an array of answers.
 *
 * Single-answer values become a one-item array, while multi-answer values
 * are returned unchanged.
 *
 * @param featureValue - Raw value read from the quiz's GeoJSON answer property.
 * @returns Normalized array of answer strings.
 */
export function getFeatureAnswers(featureValue: unknown): string[] {
  if (typeof featureValue === "string") {
    return [featureValue];
  }

  if (
    Array.isArray(featureValue) &&
    featureValue.every((value) => typeof value === "string")
  ) {
    return featureValue;
  }

  return [];
}

/**
 * Creates the user-facing answer label for a geographic feature.
 *
 * Quiz question display values are preferred when available. Multi-answer
 * features combine their values using ` / `.
 *
 * @param featureAnswers - Answers represented by the geographic feature.
 * @param quiz - Quiz definition used to resolve display values.
 * @returns User-facing feature label.
 */
export function getFeatureDisplayLabel(
  featureAnswers: string[],
  quiz: Quiz,
): string {
  return featureAnswers
    .map((answer) => {
      const matchingQuestion = quiz.questions.find(
        (question) => question.answer === answer,
      );

      return (
        matchingQuestion?.display ??
        matchingQuestion?.answer ??
        answer
      );
    })
    .join(" / ");
}

/**
 * Determines whether every quiz answer belonging to a feature has already
 * been completed.
 *
 * Both correct and wrong results count as completed answers.
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
 * every answer belonging to a geographic feature.
 *
 * This calculation is performed before React updates answerStatuses, so the
 * current answer is treated as completed explicitly.
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
