// /**
//  * Provides shared utilities for reading and evaluating quiz answers stored on
//  * geographic map features.
//  *
//  * These helpers:
//  *
//  * - Normalize single- and multi-answer feature data.
//  * - Resolve user-facing feature labels.
//  * - Determine whether a geographic feature has been fully completed.
//  * - Predict whether the current correct answer would complete a feature.
//  */

// import type { AnswerStatus, Quiz } from "@/types/quiz";

// /**
//  * Determines whether an unknown geographic feature value is an array
//  * containing only strings.
//  *
//  * @param value - Unknown feature property value.
//  * @returns Whether the value is a string array.
//  */
// function isStringArray(value: unknown): value is string[] {
//   return (
//     Array.isArray(value) &&
//     value.every((item) => typeof item === "string")
//   );
// }

// /**
//  * Normalizes a geographic feature's quiz-answer value into an array.
//  *
//  * Single-answer strings become one-item arrays. Multi-answer string arrays are
//  * returned unchanged. Missing or malformed values return an empty array.
//  *
//  * @param featureValue - Raw value read from the quiz's GeoJSON answer property.
//  * @returns Normalized quiz answers represented by the feature.
//  */
// export function getFeatureAnswers(featureValue: unknown): string[] {
//   if (typeof featureValue === "string") {
//     return [featureValue];
//   }

//   if (isStringArray(featureValue)) {
//     return featureValue;
//   }

//   return [];
// }

// /**
//  * Creates the user-facing quiz-answer label for a geographic feature.
//  *
//  * Quiz question display values are preferred when available. Multi-answer
//  * features join their represented answers using ` / `.
//  *
//  * @param featureAnswers - Answers represented by the geographic feature.
//  * @param quiz - Quiz used to resolve optional display values.
//  * @returns User-facing label for the selected feature.
//  */
// export function getFeatureDisplayLabel(
//   featureAnswers: string[],
//   quiz: Quiz,
// ): string {
//   return featureAnswers
//     .map((answer) => {
//       const matchingQuestion = quiz.questions.find(
//         (question) => question.answer === answer,
//       );

//       return (
//         matchingQuestion?.display ??
//         matchingQuestion?.answer ??
//         answer
//       );
//     })
//     .join(" / ");
// }

// /**
//  * Determines whether every quiz answer represented by a feature has already
//  * been completed.
//  *
//  * Both correct and incorrect results count as completed answers because either
//  * result means that question has already been processed by the quiz engine.
//  *
//  * @param featureAnswers - Answers represented by the geographic feature.
//  * @param answerStatuses - Completed quiz results keyed by answer value.
//  * @returns Whether every answer belonging to the feature is complete.
//  */
// export function isFeatureFullyAnswered(
//   featureAnswers: string[],
//   answerStatuses: Record<string, AnswerStatus>,
// ): boolean {
//   if (featureAnswers.length === 0) {
//     return false;
//   }

//   return featureAnswers.every(
//     (answer) => answerStatuses[answer] !== undefined,
//   );
// }

// /**
//  * Determines whether correctly answering the current question would complete
//  * every quiz answer represented by a geographic feature.
//  *
//  * This check occurs before React updates `answerStatuses`, so the current
//  * answer is treated as completed explicitly.
//  *
//  * @param featureAnswers - Answers represented by the geographic feature.
//  * @param currentAnswer - Answer belonging to the current quiz question.
//  * @param answerStatuses - Existing completed-answer statuses.
//  * @returns Whether the current answer would complete the entire feature.
//  */
// export function willFeatureBeFullyAnswered(
//   featureAnswers: string[],
//   currentAnswer: string,
//   answerStatuses: Record<string, AnswerStatus>,
// ): boolean {
//   return featureAnswers.every(
//     (answer) =>
//       answer === currentAnswer ||
//       answerStatuses[answer] !== undefined,
//   );
// }

/**
 * Provides shared utilities for reading and evaluating quiz answers stored on
 * geographic map features.
 *
 * These helpers:
 *
 * - Normalize single- and multi-answer feature data.
 * - Resolve quiz questions represented by geographic features.
 * - Resolve user-facing feature labels.
 * - Determine whether a geographic feature has been fully completed.
 * - Predict whether the current correct answer would complete a feature.
 */

import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";

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
  quiz: Quiz,
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
 * Quiz question display values are preferred when available. Multi-answer
 * features join their represented answers using ` / `.
 *
 * @param featureAnswers - Answers represented by the geographic feature.
 * @param quiz - Quiz used to resolve optional display values.
 * @returns User-facing label for the selected feature.
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
