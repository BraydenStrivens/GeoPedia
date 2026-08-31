/**
 * Renders the floating quiz interface displayed above a GeoPedia map.
 *
 * The overlay presents:
 *
 * - The quiz name.
 * - Current score and progress.
 * - The active question.
 * - Start and Show Answers controls.
 * - Skip, Stop, and Restart controls.
 * - Quiz completion results.
 *
 * QuizOverlay does not own quiz state. The parent component provides the
 * current state and control callbacks, typically from the `useQuiz` hook.
 */

"use client";
import Image from "next/image";

import QuizActionButton from "@/components/quiz/overlay/QuizActionButton";
import QuizControlButton from "@/components/quiz/overlay/QuizControlButton";
import {
  RestartIcon,
  SkipIcon,
  StopIcon,
} from "@/components/quiz/overlay/QuizControlIcons";
import { QuizQuestionPrompt } from "@/types/quiz";

/**
 * Values and callbacks required to display and control the quiz overlay.
 */
type QuizOverlayProps = {
  /** User-facing name of the current quiz. */
  quizName: string;

  /** Current question text displayed while the quiz is active. */
  question: QuizQuestionPrompt;

  /** Number of questions completed during the current attempt. */
  answeredCount: number;

  /** Total number of questions in the quiz. */
  questionCount: number;

  /** Number of correct selections made during the current attempt. */
  correctCount: number;

  /** Number of incorrect selections made during the current attempt. */
  wrongCount: number;

  /** Whether the quiz is currently running. */
  isActive: boolean;

  /** Whether every quiz question has been completed. */
  isFinished: boolean;

  /** Whether the map is ready to begin accepting quiz interaction. */
  isMapReady: boolean;

  /** Whether the inactive quiz is currently displaying answer labels. */
  isShowingAnswers: boolean;

  /**
   * Whether actions available before a quiz begins are temporarily disabled.
   *
   * Manual feature selection currently disables both Start and the normal
   * Show Answers control because that workflow provides its own answer-label
   * control and should not allow a quiz attempt to begin.
   */
  areInactiveActionsDisabled: boolean;

  /** Starts a new quiz attempt. */
  onStart: () => void;

  /** Moves the current question to the end of the queue. */
  onSkip: () => void;

  /** Restarts the current quiz attempt. */
  onRestart: () => void;

  /** Stops the current quiz attempt. */
  onStop: () => void;

  /** Toggles Show Answers while the quiz is inactive. */
  onToggleShowAnswers: () => void;
};

function QuizQuestionDisplay({
  question,
}: {
  question: QuizQuestionPrompt;
}) {
  if (question.type === "image") {
    return (
      <div className="flex items-center justify-center">
        <Image
          src={question.imageUrl}
          alt={question.alt}
          width={224}
          height={128}
          className="max-h-32 max-w-56 object-contain"
        />
      </div>
    );
  }

  return <div className="text-center">{question.text}</div>;
}

/**
 * Displays the current quiz status and the controls available for the current
 * stage of the quiz.
 *
 * @param props - Quiz overlay state and control callbacks.
 * @returns Floating quiz interface rendered above the map.
 */
export default function QuizOverlay({
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
}: QuizOverlayProps) {
  return (
    <div className="pointer-events-none absolute inset-x-0 top-3 z-10 flex flex-col items-center">
      {/* Main quiz information panel */}
      <div className="pointer-events-auto min-w-[280px] rounded-xl bg-black/20 p-2 backdrop-blur-sm">
        {/* Quiz title */}
        <div className="rounded-lg bg-white/80 px-6 py-2 text-center backdrop-blur-md">
          <h1 className="text-xl font-bold leading-tight text-gray-900">
            {quizName}
          </h1>
        </div>

        {/* Quiz progress and score */}
        <div className="flex items-center justify-between px-2">
          {/* Correct answer count */}
          <div className="flex items-center gap-1 text-sm font-semibold">
            <span>{correctCount}</span>

            <span className="text-green-600">✓</span>
          </div>

          {/* Completed question count */}
          <div className="text-center text-sm font-semibold text-gray-700">
            {answeredCount} / {questionCount}
          </div>

          {/* Incorrect answer count */}
          <div className="flex items-center gap-1 text-sm font-semibold">
            <span className="text-red-600">✕</span>

            <span>{wrongCount}</span>
          </div>
        </div>

        {/* Current question */}
        {isActive && !isFinished && (
          <div className="rounded-lg bg-white/80 px-5 py-1.5 text-center backdrop-blur-md">
            <div className="text-lg font-bold leading-tight text-gray-900">
              <QuizQuestionDisplay question={question} />
            </div>
          </div>
        )}

        {/* Inactive quiz actions */}
        {!isActive && !isFinished && (
          <div className="flex justify-center">
            {isMapReady ? (
              <div className="flex gap-2">
                {/* Start quiz */}
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

                {/* Show or hide answer labels */}
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
                className="flex items-center justify-center rounded-lg bg-white/80 px-5 py-2 backdrop-blur-md"
                aria-label="Loading map"
              >
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900" />
              </div>
            )}
          </div>
        )}

        {/* Completed quiz summary */}
        {isFinished && (
          <div className="rounded-lg bg-white/80 px-5 py-2 text-center backdrop-blur-md">
            <div className="text-base font-bold text-gray-900">
              Quiz Complete!
            </div>

            <div className="text-xs text-gray-500">
              {correctCount} / {questionCount} in{" "}
              {wrongCount + correctCount} tries
            </div>
          </div>
        )}
      </div>

      {/* Active quiz controls */}
      <div className="mt-1 flex justify-center gap-1">
        {isActive && !isFinished && (
          <>
            {/* Skip current question */}
            <QuizControlButton title="Skip question" onClick={onSkip}>
              <SkipIcon />
            </QuizControlButton>
          </>
        )}

        {isActive && (
          <>
            {/* Stop current quiz */}
            <QuizControlButton title="Stop quiz" onClick={onStop}>
              <StopIcon />
            </QuizControlButton>

            {/* Restart quiz */}
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
