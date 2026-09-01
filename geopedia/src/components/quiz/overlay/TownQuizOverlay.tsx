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
 * - Skip, Stop, and Restart controls beneath the main overlay while running.
 * - A centered final summary after every question has been answered.
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

  /** Whether the quiz is currently running. */
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
 * Formats a normalized score as a rounded percentage.
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
 * Renders one two-line town quiz statistic.
 */
function Statistic({
  primary,
  secondary,
}: {
  /** Primary, more prominent statistic. */
  primary: string;

  /** Secondary statistic displayed beneath it. */
  secondary: string;
}) {
  return (
    <div className="flex flex-col text-sm font-semibold leading-tight text-gray-700">
      <span>{primary}</span>

      <span className="text-xs text-gray-500">{secondary}</span>
    </div>
  );
}

/**
 * Renders GeoPedia's town quiz information and lifecycle controls.
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
   * While a question is active, `answeredCount` describes completed questions,
   * so the question currently being shown is one position later.
   *
   * Completed quizzes remain fixed at the total question count.
   */
  const currentQuestionNumber = isFinished
    ? questionCount
    : Math.min(answeredCount + 1, questionCount);

  return (
    <div className="pointer-events-none absolute inset-x-0 top-3 z-10 flex flex-col items-center">
      {/* Main town quiz information panel */}
      <div className="pointer-events-auto min-w-[320px] rounded-xl bg-black/20 p-2 backdrop-blur-sm">
        {/* Quiz title */}
        <div className="rounded-lg bg-white/80 px-6 py-2 text-center backdrop-blur-md">
          <h1 className="text-xl font-bold leading-tight text-gray-900">
            {quizName}
          </h1>
        </div>

        {/* Inactive quiz actions */}
        {!isActive && !isFinished && (
          <div className="mt-2 flex justify-center">
            <QuizActionButton onClick={onStart}>
              Start
            </QuizActionButton>
          </div>
        )}

        {/* Running quiz information */}
        {isActive && !isFinished && (
          <>
            {/* Current town */}
            <div className="mt-2 rounded-lg bg-white/80 px-5 py-1.5 text-center backdrop-blur-md">
              <div className="text-lg font-bold leading-tight text-gray-900">
                {currentTownName}
              </div>
            </div>

            {/* Previous result, progress, and cumulative result */}
            <div className="mt-1 grid grid-cols-3 items-center px-2">
              {/* Last answer */}
              <div className="text-left">
                <div className="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-gray-500">
                  Last
                </div>

                {lastScore !== undefined &&
                lastDistanceKm !== undefined ? (
                  <Statistic
                    primary={formatScore(lastScore)}
                    secondary={formatDistance(lastDistanceKm)}
                  />
                ) : (
                  <Statistic primary="—" secondary="—" />
                )}
              </div>

              {/* Current question */}
              <div className="text-center text-sm font-semibold text-gray-700">
                {currentQuestionNumber} / {questionCount}
              </div>

              {/* Aggregate attempt statistics */}
              <div className="text-right">
                <div className="mb-0.5 text-[10px] font-bold uppercase tracking-wide text-gray-500">
                  Total
                </div>

                <Statistic
                  primary={formatScore(averageScore)}
                  secondary={formatDistance(totalDistanceKm)}
                />
              </div>
            </div>
          </>
        )}

        {/* Finished quiz summary */}
        {isFinished && (
          <div className="mt-2 rounded-lg bg-white/80 px-5 py-2 text-center backdrop-blur-md">
            {/* Final question counter */}
            <div className="text-sm font-semibold text-gray-700">
              {questionCount} / {questionCount}
            </div>

            {/* Final aggregate results */}
            <div className="mt-1">
              <div className="text-lg font-bold text-gray-900">
                {formatScore(averageScore)}
              </div>

              <div className="text-sm font-semibold text-gray-600">
                {formatDistance(totalDistanceKm)} total
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quiz lifecycle controls beneath the main overlay */}
      <div className="mt-1 flex justify-center gap-1">
        {/* Running quiz controls */}
        {isActive && !isFinished && (
          <>
            <QuizControlButton title="Skip question" onClick={onSkip}>
              <SkipIcon />
            </QuizControlButton>

            <QuizControlButton title="Stop quiz" onClick={onStop}>
              <StopIcon />
            </QuizControlButton>

            <QuizControlButton
              title="Restart quiz"
              onClick={onRestart}
            >
              <RestartIcon />
            </QuizControlButton>
          </>
        )}

        {/* Completed quiz controls */}
        {isFinished && (
          <>
            <QuizControlButton title="Stop quiz" onClick={onStop}>
              <StopIcon />
            </QuizControlButton>

            <QuizControlButton
              title="Restart quiz"
              onClick={onRestart}
            >
              <RestartIcon />
            </QuizControlButton>
          </>
        )}
      </div>
    </div>
  );
}
