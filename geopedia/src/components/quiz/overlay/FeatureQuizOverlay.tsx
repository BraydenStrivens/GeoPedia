/**
 * Renders the floating quiz interface used by GeoPedia feature quizzes.
 *
 * Feature quizzes use correct and incorrect map selections to measure quiz
 * performance. The overlay presents:
 *
 * - The quiz name.
 * - Current score and progress.
 * - The active feature question.
 * - Start and Show Answers controls while inactive.
 * - Skip, Stop, and Restart controls during an attempt.
 * - Quiz completion results.
 *
 * Manual feature selection can temporarily disable the normal inactive Start
 * and Show Answers actions because that grouping workflow owns map interaction
 * and provides its own answer-label control.
 *
 * Shared overlay positioning and title presentation are delegated to reusable
 * overlay components. Feature-specific scoring, question presentation,
 * completion results, and inactive-action behavior remain owned here.
 *
 * This component owns no quiz state. Its parent supplies the current
 * feature-quiz state and lifecycle callbacks.
 */

"use client";

import QuizActionButton from "@/components/quiz/overlay/shared/QuizActionButton";
import QuizControlButton from "@/components/quiz/overlay/shared/QuizControlButton";
import {
  RestartIcon,
  SkipIcon,
  StopIcon,
} from "@/components/quiz/overlay/shared/QuizControlIcons";
import QuizOverlayShell from "@/components/quiz/overlay/shared/QuizOverlayShell";
import QuizOverlayTitle from "@/components/quiz/overlay/shared/QuizOverlayTitle";
import QuizQuestionDisplay from "@/components/quiz/overlay/shared/QuizQuestionDisplay";
import type { QuizQuestionPrompt } from "@/types/quiz";

/**
 * Values and callbacks required to display and control the feature quiz overlay.
 */
type FeatureQuizOverlayProps = {
  /** User-facing name of the current feature quiz. */
  quizName: string;

  /** Current feature question displayed while the quiz is active. */
  question: QuizQuestionPrompt;

  /** Number of questions completed during the current attempt. */
  answeredCount: number;

  /** Total number of questions in the quiz. */
  questionCount: number;

  /** Number of correct selections made during the current attempt. */
  correctCount: number;

  /** Number of incorrect selections made during the current attempt. */
  wrongCount: number;

  /** Whether the feature quiz is currently running. */
  isActive: boolean;

  /** Whether every feature quiz question has been completed. */
  isFinished: boolean;

  /** Whether the map is ready to begin accepting quiz interaction. */
  isMapReady: boolean;

  /** Whether the inactive quiz is currently displaying answer labels. */
  isShowingAnswers: boolean;

  /**
   * Whether actions available before a quiz begins are temporarily disabled.
   *
   * Manual feature selection disables both Start and the normal Show Answers
   * control because that workflow provides its own answer-label control and
   * should not allow a quiz attempt to begin.
   */
  areInactiveActionsDisabled: boolean;

  /** Starts a new feature quiz attempt. */
  onStart: () => void;

  /** Moves the current question to the end of the queue. */
  onSkip: () => void;

  /** Restarts the current feature quiz attempt. */
  onRestart: () => void;

  /** Stops the current feature quiz attempt. */
  onStop: () => void;

  /** Toggles Show Answers while the feature quiz is inactive. */
  onToggleShowAnswers: () => void;
};

/**
 * Displays the current feature quiz status and the controls available for the
 * current stage of the attempt.
 *
 * @param props - Feature quiz overlay state and control callbacks.
 * @returns Floating feature quiz interface rendered above the map.
 */
export default function FeatureQuizOverlay({
  quizName,
  question,
  answeredCount,
  questionCount,
  correctCount,
  wrongCount,
  isActive,
  isFinished,
  isMapReady,
  isShowingAnswers,
  areInactiveActionsDisabled,
  onStart,
  onSkip,
  onRestart,
  onStop,
  onToggleShowAnswers,
}: FeatureQuizOverlayProps) {
  /**
   * Lifecycle controls rendered beneath the primary feature quiz panel.
   *
   * Skip is available only while there is an unanswered active question. Stop
   * and Restart remain available throughout the active attempt, including the
   * completed-results state.
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
      minWidthClassName="min-w-[280px]"
      controls={lifecycleControls}
    >
      {/* Shared quiz title */}
      <QuizOverlayTitle quizName={quizName} />

      {/* Quiz progress and score */}
      <div className="flex items-center justify-between px-2">
        {/* Correct answer count */}
        <div className="flex items-center gap-1 text-sm font-semibold">
          <span>{correctCount}</span>
          <span className="text-green-600">✓</span>
        </div>

        {/* Completed question count */}
        <div className="text-center text-sm font-semibold text-text-secondary">
          {answeredCount} / {questionCount}
        </div>

        {/* Incorrect answer count */}
        <div className="flex items-center gap-1 text-sm font-semibold">
          <span className="text-red-600">✕</span>
          <span>{wrongCount}</span>
        </div>
      </div>

      {/* Current feature question */}
      {isActive && !isFinished && (
        <div className="rounded-lg bg-background-1/80 px-5 py-1.5 text-center backdrop-blur-md">
          <div className="text-lg font-bold leading-tight text-text">
            <QuizQuestionDisplay question={question} />
          </div>
        </div>
      )}

      {/* Inactive feature quiz actions */}
      {!isActive && !isFinished && (
        <div className="flex justify-center">
          {isMapReady ? (
            <div className="flex gap-2">
              {/* Start feature quiz */}
              <QuizActionButton
                isDisabled={areInactiveActionsDisabled}
                title={
                  areInactiveActionsDisabled
                    ? "Finish or cancel manual selection before starting the quiz."
                    : undefined
                }
                onClick={onStart}
              >
                Start
              </QuizActionButton>

              {/* Show or hide inactive feature answer labels */}
              <QuizActionButton
                isDisabled={areInactiveActionsDisabled}
                title={
                  areInactiveActionsDisabled
                    ? "Use the Manual Selection Show Answers control while selecting features."
                    : undefined
                }
                onClick={onToggleShowAnswers}
              >
                {isShowingAnswers ? "Hide Answers" : "Show Answers"}
              </QuizActionButton>
            </div>
          ) : (
            /* Map loading indicator */
            <div
              className="flex items-center justify-center rounded-lg bg-background-1/80 px-5 py-2 backdrop-blur-md"
              aria-label="Loading map"
            >
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-border border-t-text" />
            </div>
          )}
        </div>
      )}

      {/* Completed feature quiz summary */}
      {isFinished && (
        <div className="rounded-lg bg-background-1/80 px-5 py-2 text-center backdrop-blur-md">
          <div className="text-base font-bold text-text">
            Quiz Complete!
          </div>

          <div className="text-xs text-text-secondary">
            {correctCount} / {questionCount} in{" "}
            {wrongCount + correctCount} tries
          </div>
        </div>
      )}
    </QuizOverlayShell>
  );
}
