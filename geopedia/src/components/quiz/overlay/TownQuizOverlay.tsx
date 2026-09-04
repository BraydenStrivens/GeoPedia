/**
 * Renders the floating quiz interface used by GeoPedia town quizzes.
 *
 * Town quizzes use geographic-distance scoring rather than correct/incorrect
 * feature selection, so their overlay presents statistics tailored to location
 * guesses:
 *
 * - The quiz name.
 * - The current town while a quiz is running.
 * - The previous guess's percentage score and geographic error.
 * - Current question progress.
 * - Average percentage score and cumulative geographic error.
 * - A Start control while the quiz is inactive.
 * - Skip, Stop, and Restart controls while an attempt is active.
 * - A centered final summary after every question has been answered.
 *
 * Shared overlay positioning and title presentation are delegated to reusable
 * overlay components. Town-specific statistics, formatting, results, and
 * lifecycle behavior remain owned by this component.
 *
 * This component owns no quiz state. All quiz state and lifecycle actions are
 * supplied by the parent town quiz client.
 */

"use client";

import QuizActionButton from "./shared/QuizActionButton";
import QuizControlButton from "./shared/QuizControlButton";
import {
  RestartIcon,
  SkipIcon,
  StopIcon,
} from "./shared/QuizControlIcons";
import QuizOverlayShell from "./shared/QuizOverlayShell";
import QuizOverlayTitle from "./shared/QuizOverlayTitle";

/**
 * Values and callbacks required to render the town quiz overlay.
 */
type TownQuizOverlayProps = {
  /** User-facing name of the town quiz. */
  quizName: string;

  /** Name of the town currently being located. */
  currentTownName?: string;

  /** Number of questions already answered during this attempt. */
  answeredCount: number;

  /** Total number of questions in the current town quiz group. */
  questionCount: number;

  /** Percentage score from the most recently answered question, from 0 to 1. */
  lastScore?: number;

  /** Geographic error of the most recent answer, measured in kilometers. */
  lastDistanceKm?: number;

  /** Average percentage score across every answered question, from 0 to 1. */
  averageScore: number;

  /** Sum of geographic error across every answered question, in kilometers. */
  totalDistanceKm: number;

  /** Whether the quiz is currently running or displaying completed results. */
  isActive: boolean;

  /** Whether every question in the current attempt has been completed. */
  isFinished: boolean;

  /** Starts a fresh town quiz attempt. */
  onStart: () => void;

  /** Moves the current town to the end of the unanswered question queue. */
  onSkip: () => void;

  /** Stops the current quiz attempt. */
  onStop: () => void;

  /** Restarts the current quiz attempt from the beginning. */
  onRestart: () => void;
};

/**
 * Props required by one town quiz statistic display.
 */
type TownQuizStatisticProps = {
  /** Primary, more prominent statistic. */
  primary: string;

  /** Secondary statistic displayed beneath the primary value. */
  secondary: string;
};

/**
 * Formats a normalized town quiz score as a rounded percentage.
 *
 * @param score - Score from 0 through 1.
 * @returns User-facing percentage.
 */
function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

/**
 * Formats geographic error using meters for close guesses and kilometers for
 * larger guesses.
 *
 * Distances below one kilometer are easier to understand in meters. Kilometer
 * values below 100 retain one decimal place while larger errors are rounded to
 * whole kilometers to avoid unnecessary precision.
 *
 * @param distanceKm - Geographic distance in kilometers.
 * @returns User-facing distance string.
 */
function formatDistance(distanceKm: number): string {
  if (distanceKm < 1) {
    return `${Math.round(distanceKm * 1000)} m`;
  }

  if (distanceKm < 100) {
    return `${distanceKm.toFixed(1)} km`;
  }

  return `${Math.round(distanceKm)} km`;
}

/**
 * Renders one two-line statistic used by the town quiz overlay.
 *
 * Town quiz statistics pair a prominent score with a secondary geographic
 * distance, such as the previous guess result or cumulative attempt result.
 *
 * @param props - Primary and secondary statistic values.
 * @returns Two-line town quiz statistic.
 */
function TownQuizStatistic({
  primary,
  secondary,
}: TownQuizStatisticProps) {
  return (
    <div className="flex flex-col text-sm font-semibold leading-tight text-text">
      <span>{primary}</span>

      <span className="text-xs text-text">{secondary}</span>
    </div>
  );
}

/**
 * Renders GeoPedia's town quiz information and lifecycle controls.
 *
 * @param props - Town quiz state, statistics, and lifecycle callbacks.
 * @returns Floating town quiz interface rendered above the map.
 */
export default function TownQuizOverlay({
  quizName,
  currentTownName,
  answeredCount,
  questionCount,
  lastScore,
  lastDistanceKm,
  averageScore,
  totalDistanceKm,
  isActive,
  isFinished,
  onStart,
  onSkip,
  onStop,
  onRestart,
}: TownQuizOverlayProps) {
  /**
   * Question number currently represented by the overlay.
   *
   * While a question is active, `answeredCount` describes only completed
   * questions, so the currently displayed question is one position later.
   * Completed quizzes remain fixed at the total question count.
   */
  const currentQuestionNumber = isFinished
    ? questionCount
    : Math.min(answeredCount + 1, questionCount);

  /**
   * Shared lifecycle controls displayed beneath the town quiz information panel.
   *
   * Skip is available only while an unanswered question is active. Stop and
   * Restart remain available for the duration of the active attempt, including
   * the completed-results state.
   */
  const lifecycleControls =
    isActive || isFinished ? (
      <>
        {isActive && !isFinished && (
          <QuizControlButton title="Skip question" onClick={onSkip}>
            <SkipIcon />
          </QuizControlButton>
        )}

        <QuizControlButton title="Stop quiz" onClick={onStop}>
          <StopIcon />
        </QuizControlButton>

        <QuizControlButton title="Restart quiz" onClick={onRestart}>
          <RestartIcon />
        </QuizControlButton>
      </>
    ) : undefined;

  return (
    <QuizOverlayShell
      minWidthClassName="min-w-[320px]"
      controls={lifecycleControls}
    >
      {/* Shared quiz title */}
      <QuizOverlayTitle quizName={quizName} />

      {/* Inactive quiz actions */}
      {!isActive && !isFinished && (
        <div className="mt-2 flex justify-center">
          <QuizActionButton onClick={onStart}>Start</QuizActionButton>
        </div>
      )}

      {/* Running quiz information */}
      {isActive && !isFinished && (
        <>
          {/* Town currently being located */}
          <div className="mt-2 rounded-lg bg-background-1/80 px-5 py-1.5 text-center backdrop-blur-md">
            <div className="text-lg font-bold leading-tight text-text">
              {currentTownName}
            </div>
          </div>

          {/* Previous result, question progress, and cumulative result */}
          <div className="mt-1 grid grid-cols-3 items-center px-2">
            {/* Most recently answered town */}
            <div className="text-left">
              <div className="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-text-secondary">
                Last
              </div>

              {lastScore !== undefined &&
              lastDistanceKm !== undefined ? (
                <TownQuizStatistic
                  primary={formatScore(lastScore)}
                  secondary={formatDistance(lastDistanceKm)}
                />
              ) : (
                <TownQuizStatistic primary="—" secondary="—" />
              )}
            </div>

            {/* Current question position */}
            <div className="text-center text-sm font-semibold text-text">
              {currentQuestionNumber} / {questionCount}
            </div>

            {/* Aggregate attempt statistics */}
            <div className="text-right">
              <div className="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-text-secondary">
                Total
              </div>

              <TownQuizStatistic
                primary={formatScore(averageScore)}
                secondary={formatDistance(totalDistanceKm)}
              />
            </div>
          </div>
        </>
      )}

      {/* Finished quiz summary */}
      {isFinished && (
        <div className="mt-2 rounded-lg bg-background-1/80 px-5 py-2 text-center backdrop-blur-md">
          {/* Final question counter */}
          <div className="text-sm font-semibold text-text-secondary">
            {questionCount} / {questionCount}
          </div>

          {/* Final aggregate results */}
          <div className="mt-1">
            <div className="text-lg font-bold text-text">
              {formatScore(averageScore)}
            </div>

            <div className="text-sm font-semibold text-text-secondary">
              {formatDistance(totalDistanceKm)} total
            </div>
          </div>
        </div>
      )}
    </QuizOverlayShell>
  );
}
