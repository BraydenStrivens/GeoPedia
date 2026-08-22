/**
 * Builds MapLibre color expressions for quiz feature progress.
 *
 * Features may represent either one quiz answer or multiple answers.
 * Multi-answer features gradually change color as their associated
 * questions are answered.
 *
 * Accuracy determines the balance between red and green, while completion
 * determines how strongly that result replaces the map's normal fill.
 */

import type { ExpressionSpecification } from "maplibre-gl";

import type { AnswerStatus, AnswerType } from "@/types/quiz";

const CORRECT_RGB = [34, 197, 94];
const WRONG_RGB = [239, 68, 68];

type RGB = [number, number, number];

/**
 * Converts a six-digit hex color such as "#969696" into RGB values.
 */
function hexToRgb(hex: string): RGB {
  const normalized = hex.replace("#", "");

  return [
    parseInt(normalized.slice(0, 2), 16),
    parseInt(normalized.slice(2, 4), 16),
    parseInt(normalized.slice(4, 6), 16),
  ];
}

/**
 * Creates a MapLibre expression that checks whether a feature contains
 * a particular quiz answer.
 *
 * Single-answer features compare the property directly, while
 * multi-answer features check whether the answer exists in an array.
 */
function createAnswerMatchExpression(
  answerProperty: string,
  answer: string,
  answerType: AnswerType,
): unknown[] {
  if (answerType === "multiple") {
    return ["in", answer, ["get", answerProperty]];
  }

  return ["==", ["get", answerProperty], answer];
}

/**
 * Counts the answers belonging to a feature that have a particular status.
 */
function createStatusCountExpression(
  answerStatuses: Record<string, AnswerStatus>,
  answerProperty: string,
  answerType: AnswerType,
  statusToCount: AnswerStatus,
): unknown {
  const expressions = Object.entries(answerStatuses)
    .filter(([, status]) => status === statusToCount)
    .map(([answer]) => [
      "case",
      createAnswerMatchExpression(answerProperty, answer, answerType),
      1,
      0,
    ]);

  if (expressions.length === 0) {
    return 0;
  }

  if (expressions.length === 1) {
    return expressions[0];
  }

  return ["+", ...expressions];
}

/**
 * Returns the total number of quiz answers represented by a feature.
 *
 * Single-answer features always represent one answer. Multi-answer
 * features use the length of their answer array.
 */
function createTotalAnswerCountExpression(
  answerProperty: string,
  answerType: AnswerType,
): unknown {
  if (answerType === "multiple") {
    return ["length", ["get", answerProperty]];
  }

  return 1;
}

/**
 * Creates the fill-color expression used by quiz features.
 *
 * The color is based on two values:
 *
 * - accuracy: how many attempted answers were correct
 * - completion: how many of the feature's total answers were attempted
 *
 * Accuracy blends the result between red and green. Completion then
 * blends that result with the map's normal feature color.
 */
export function createFeatureColorExpression(
  answerStatuses: Record<string, AnswerStatus>,
  answerProperty: string,
  answerType: AnswerType,
  normalColor: string,
  showShading: boolean,
  visibleAnswer?: string,
): ExpressionSpecification {
  const [normalR, normalG, normalB] = hexToRgb(normalColor);

  const correctCount = createStatusCountExpression(
    answerStatuses,
    answerProperty,
    answerType,
    "correct",
  );

  const wrongCount = createStatusCountExpression(
    answerStatuses,
    answerProperty,
    answerType,
    "wrong",
  );

  const totalCount = createTotalAnswerCountExpression(
    answerProperty,
    answerType,
  );

  const answeredCount = ["+", correctCount, wrongCount];

  const hasAnswers = [">", answeredCount, 0];

  /*
   * Accuracy ranges from 0 to 1.
   *
   * 0   = every attempted answer was wrong
   * 0.5 = half correct / half wrong
   * 1   = every attempted answer was correct
   */
  const accuracy = ["/", correctCount, answeredCount];

  /*
   * Completion ranges from 0 to 1.
   *
   * For a two-answer feature:
   * one answered  = 0.5
   * both answered = 1
   */
  const completion = ["/", answeredCount, totalCount];

  /*
   * Blend red and green according to accuracy.
   */
  const resultR = [
    "+",
    ["*", WRONG_RGB[0], ["-", 1, accuracy]],
    ["*", CORRECT_RGB[0], accuracy],
  ];

  const resultG = [
    "+",
    ["*", WRONG_RGB[1], ["-", 1, accuracy]],
    ["*", CORRECT_RGB[1], accuracy],
  ];

  const resultB = [
    "+",
    ["*", WRONG_RGB[2], ["-", 1, accuracy]],
    ["*", CORRECT_RGB[2], accuracy],
  ];

  /*
   * Blend the result color with the normal map color according to
   * how much of the feature has been completed.
   */
  const colorStrength = ["+", 0.25, ["*", completion, 0.75]];

  const finalR = [
    "+",
    ["*", normalR, ["-", 1, colorStrength]],
    ["*", resultR, colorStrength],
  ];

  const finalG = [
    "+",
    ["*", normalG, ["-", 1, colorStrength]],
    ["*", resultG, colorStrength],
  ];

  const finalB = [
    "+",
    ["*", normalB, ["-", 1, colorStrength]],
    ["*", resultB, colorStrength],
  ];

  /*
   * Unanswered features use the normal map color. Once at least one
   * answer has been attempted, the feature uses its calculated
   * quiz-progress color.
   */
  const baseR = ["case", hasAnswers, finalR, normalR];

  const baseG = ["case", hasAnswers, finalG, normalG];

  const baseB = ["case", hasAnswers, finalB, normalB];

  const normalMapColor = [
    "rgba",
    normalR,
    normalG,
    normalB,
    showShading ? 1 : 0,
  ];

  // Only show normal map color if shading is enabled
  const baseAlpha = ["case", hasAnswers, 1, showShading ? 1 : 0];

  const baseColor = ["rgba", baseR, baseG, baseB, baseAlpha];

  if (!visibleAnswer) {
    return baseColor as unknown as ExpressionSpecification;
  }

  const isVisibleFeature = createAnswerMatchExpression(
    answerProperty,
    visibleAnswer,
    answerType,
  );

  const hardModeColor = [
    "case",

    // The feature containing the most recently answered question
    // keeps its complete quiz-progress color.
    isVisibleFeature,
    baseColor,

    // Every other feature returns to its ordinary map appearance.
    normalMapColor,
  ];

  return hardModeColor as unknown as ExpressionSpecification;
}
