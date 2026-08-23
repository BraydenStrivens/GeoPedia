/**
 * Builds MapLibre color expressions for quiz feature progress.
 *
 * Quiz features can represent either one answer or multiple answers.
 * Multi-answer features gradually transition from the normal map color
 * toward red/green result colors as their associated questions are completed.
 *
 * The final feature color is determined by:
 *
 * - Accuracy: the proportion of completed answers that were correct.
 * - Completion: the proportion of the feature's total answers that have
 *   been completed.
 * - Quiz mode: Normal Mode displays all completed results, while Hard Mode
 *   displays only the most recently completed answer's feature.
 * - Shading: controls whether unanswered features use the normal map fill.
 */

import type { ExpressionSpecification } from "maplibre-gl";

import type { AnswerStatus, AnswerType } from "@/types/quiz";
import type { QuizMode } from "@/types/quizSettings";

/**
 * RGB tuple used when constructing MapLibre color expressions.
 */
type RGB = [number, number, number];

/**
 * Intermediate MapLibre expression representation used while composing
 * nested expressions.
 */
type MapExpression = unknown[];

/** RGB value used for correct quiz results. */
const CORRECT_RGB: RGB = [34, 197, 94];

/** RGB value used for incorrect quiz results. */
const WRONG_RGB: RGB = [239, 68, 68];

/**
 * Converts a six-digit hexadecimal color into an RGB tuple.
 *
 * @param hex - Hex color such as `#969696`.
 * @returns Numeric red, green, and blue channel values.
 */
function hexToRgb(hex: string): RGB {
  const normalizedHex = hex.replace("#", "");

  return [
    parseInt(normalizedHex.slice(0, 2), 16),
    parseInt(normalizedHex.slice(2, 4), 16),
    parseInt(normalizedHex.slice(4, 6), 16),
  ];
}

/**
 * Creates a MapLibre expression that checks whether a geographic feature
 * represents a particular quiz answer.
 *
 * Single-answer features compare their answer property directly.
 * Multi-answer features check whether the answer exists in an array.
 *
 * @param answerProperty - GeoJSON property containing the feature's answers.
 * @param answer - Quiz answer to search for.
 * @param answerType - Whether the feature stores one answer or many.
 * @returns A MapLibre boolean expression that matches the answer.
 */
function createAnswerMatchExpression(
  answerProperty: string,
  answer: string,
  answerType: AnswerType,
): MapExpression {
  if (answerType === "multiple") {
    return ["in", answer, ["get", answerProperty]];
  }

  return ["==", ["get", answerProperty], answer];
}

/**
 * Creates a MapLibre expression that counts answers on a feature having a
 * particular result status.
 *
 * @param answerStatuses - Completed quiz results keyed by answer value.
 * @param answerProperty - GeoJSON property containing the feature's answers.
 * @param answerType - Whether each feature represents one or many answers.
 * @param statusToCount - Answer result that should contribute to the count.
 * @returns A MapLibre numeric expression representing the matching count.
 */
function createStatusCountExpression(
  answerStatuses: Record<string, AnswerStatus>,
  answerProperty: string,
  answerType: AnswerType,
  statusToCount: AnswerStatus,
): number | MapExpression {
  const statusExpressions = Object.entries(answerStatuses)
    .filter(([, status]) => status === statusToCount)
    .map(([answer]) => [
      "case",
      createAnswerMatchExpression(answerProperty, answer, answerType),
      1,
      0,
    ]);

  if (statusExpressions.length === 0) {
    return 0;
  }

  if (statusExpressions.length === 1) {
    return statusExpressions[0];
  }

  return ["+", ...statusExpressions];
}

/**
 * Creates a MapLibre expression representing the number of quiz answers
 * belonging to a feature.
 *
 * @param answerProperty - GeoJSON property containing the feature's answers.
 * @param answerType - Whether the feature stores one answer or many.
 * @returns `1` for single-answer features or the feature array length for
 * multi-answer features.
 */
function createTotalAnswerCountExpression(
  answerProperty: string,
  answerType: AnswerType,
): number | MapExpression {
  if (answerType === "multiple") {
    return ["length", ["get", answerProperty]];
  }

  return 1;
}

/**
 * Creates the MapLibre fill-color expression used by quiz features.
 *
 * Accuracy determines the red-to-green balance of a completed feature.
 * Completion determines how strongly that result color replaces the map's
 * normal fill color.
 *
 * In Normal Mode, every completed feature displays its accumulated result.
 * In Hard Mode, only the feature containing `visibleAnswer` displays quiz
 * result coloring.
 *
 * @param answerStatuses - Completed quiz results keyed by answer value.
 * @param answerProperty - GeoJSON property containing feature answers.
 * @param answerType - Whether each feature represents one or multiple answers.
 * @param normalColor - Default map fill color in hexadecimal format.
 * @param showShading - Whether unanswered features should display normal fill.
 * @param mode - Current quiz presentation mode.
 * @param visibleAnswer - Answer whose feature should remain visible in Hard
 * Mode.
 * @returns A MapLibre fill-color expression.
 */
export function createFeatureColorExpression(
  answerStatuses: Record<string, AnswerStatus>,
  answerProperty: string,
  answerType: AnswerType,
  normalColor: string,
  showShading: boolean,
  mode: QuizMode,
  visibleAnswer?: string,
): ExpressionSpecification {
  const [normalRed, normalGreen, normalBlue] = hexToRgb(normalColor);

  const correctAnswerCount = createStatusCountExpression(
    answerStatuses,
    answerProperty,
    answerType,
    "correct",
  );

  const wrongAnswerCount = createStatusCountExpression(
    answerStatuses,
    answerProperty,
    answerType,
    "wrong",
  );

  const totalAnswerCount = createTotalAnswerCountExpression(
    answerProperty,
    answerType,
  );

  const completedAnswerCount = [
    "+",
    correctAnswerCount,
    wrongAnswerCount,
  ];

  const hasCompletedAnswers = [">", completedAnswerCount, 0];

  /*
   * Accuracy ranges from 0 to 1:
   *
   * 0   -> every completed answer was wrong
   * 0.5 -> half correct and half wrong
   * 1   -> every completed answer was correct
   */
  const accuracy = ["/", correctAnswerCount, completedAnswerCount];

  /*
   * Completion ranges from 0 to 1:
   *
   * For a two-answer feature:
   * 0.5 -> one answer completed
   * 1   -> both answers completed
   */
  const completion = ["/", completedAnswerCount, totalAnswerCount];

  /*
   * Blend WRONG_RGB and CORRECT_RGB according to accuracy.
   */
  const resultRed = [
    "+",
    ["*", WRONG_RGB[0], ["-", 1, accuracy]],
    ["*", CORRECT_RGB[0], accuracy],
  ];

  const resultGreen = [
    "+",
    ["*", WRONG_RGB[1], ["-", 1, accuracy]],
    ["*", CORRECT_RGB[1], accuracy],
  ];

  const resultBlue = [
    "+",
    ["*", WRONG_RGB[2], ["-", 1, accuracy]],
    ["*", CORRECT_RGB[2], accuracy],
  ];

  /*
   * Partially completed features still receive noticeable result coloring.
   *
   * colorStrength begins at 0.25 and increases to 1 as completion reaches 1.
   */
  const colorStrength = ["+", 0.25, ["*", completion, 0.75]];

  /*
   * Blend the quiz result color with the normal map color according to the
   * calculated result strength.
   */
  const blendedRed = [
    "+",
    ["*", normalRed, ["-", 1, colorStrength]],
    ["*", resultRed, colorStrength],
  ];

  const blendedGreen = [
    "+",
    ["*", normalGreen, ["-", 1, colorStrength]],
    ["*", resultGreen, colorStrength],
  ];

  const blendedBlue = [
    "+",
    ["*", normalBlue, ["-", 1, colorStrength]],
    ["*", resultBlue, colorStrength],
  ];

  /* Features without completed answers retain the normal map color. */
  const displayedRed = [
    "case",
    hasCompletedAnswers,
    blendedRed,
    normalRed,
  ];

  const displayedGreen = [
    "case",
    hasCompletedAnswers,
    blendedGreen,
    normalGreen,
  ];

  const displayedBlue = [
    "case",
    hasCompletedAnswers,
    blendedBlue,
    normalBlue,
  ];

  /*  Normal unanswered feature appearance. */
  const normalMapColor = [
    "rgba",
    normalRed,
    normalGreen,
    normalBlue,
    showShading ? 1 : 0,
  ];

  /* Completed answers remain visible even when normal map shading is disabled. */
  const featureAlpha = [
    "case",
    hasCompletedAnswers,
    1,
    showShading ? 1 : 0,
  ];

  const accumulatedResultColor = [
    "rgba",
    displayedRed,
    displayedGreen,
    displayedBlue,
    featureAlpha,
  ];

  /** Normal Mode displays all accumulated quiz results. */
  if (mode !== "hard") {
    return accumulatedResultColor as unknown as ExpressionSpecification;
  }

  /**
   * Hard Mode may temporarily have no visible result after a skip or recycled
   * miss. In that state, every feature returns to its normal appearance.
   */
  if (!visibleAnswer) {
    return normalMapColor as unknown as ExpressionSpecification;
  }

  const isVisibleFeature = createAnswerMatchExpression(
    answerProperty,
    visibleAnswer,
    answerType,
  );

  /*
   * Hard Mode displays quiz-result coloring only for the feature containing
   * the most recently completed answer.
   */
  const hardModeColor = [
    "case",
    isVisibleFeature,
    accumulatedResultColor,
    normalMapColor,
  ];

  return hardModeColor as unknown as ExpressionSpecification;
}
