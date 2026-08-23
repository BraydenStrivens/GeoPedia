/**
 * Renders the floating quiz interface displayed above a GeoPedia map.
 *
 * The overlay presents:
 *
 * - The quiz name.
 * - Current score and progress.
 * - The active question.
 * - Start and Show Answers controls.
 * - Skip, stop, and restart controls.
 * - Quiz completion results.
 *
 * QuizOverlay does not own quiz state. The parent component provides the
 * current state and control callbacks, typically from the `useQuiz` hook.
 */

"use client";

import type { ReactNode } from "react";

/**
 * Values and callbacks required to display and control the quiz overlay.
 */
type QuizOverlayProps = {
  /** User-facing name of the current quiz. */
  quizName: string;

  /** Current question text displayed while the quiz is active. */
  question: string;

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

  /** Whether the inactive quiz is currently displaying Show Answers labels. */
  isShowingAnswers: boolean;

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

/**
 * Props shared by the large text buttons displayed while the quiz is inactive.
 */
type QuizActionButtonProps = {
  /** Button text displayed to the user. */
  children: ReactNode;

  /** Function called when the button is selected. */
  onClick: () => void;
};

/**
 * Props shared by compact icon-based quiz controls.
 */
type QuizControlButtonProps = {
  /** Accessible tooltip describing the control. */
  title: string;

  /** Icon displayed inside the button. */
  children: ReactNode;

  /** Function called when the control is selected. */
  onClick: () => void;
};

/**
 * Shared appearance of the large action buttons shown before a quiz begins.
 *
 * Keeping this style in one place makes future changes to the Start and
 * Show Answers controls apply consistently.
 */
const QUIZ_ACTION_BUTTON_CLASSES = [
  "rounded-lg",
  "bg-white/80",
  "px-5",
  "py-1.5",
  "text-center",
  "text-lg",
  "font-bold",
  "leading-tight",
  "text-gray-900",
  "backdrop-blur-md",
  "transition",
  "hover:bg-gray-300",
].join(" ");

/**
 * Shared appearance of the compact icon controls displayed beneath the quiz.
 *
 * Skip, Stop, and Restart intentionally use the same control style.
 */
const QUIZ_CONTROL_BUTTON_CLASSES = [
  "pointer-events-auto",
  "flex",
  "h-6",
  "w-6",
  "items-center",
  "justify-center",
  "rounded-md",
  "bg-white/80",
  "text-gray-600",
  "shadow-sm",
  "backdrop-blur-sm",
  "transition",
  "hover:bg-gray-300",
  "hover:text-black",
  "active:scale-90",
].join(" ");

/**
 * Large text button used for actions available while the quiz is inactive.
 *
 * @param props - Action button properties.
 * @param props.children - Text displayed inside the button.
 * @param props.onClick - Callback invoked when the button is selected.
 * @returns A consistently styled quiz action button.
 */
function QuizActionButton({
  children,
  onClick,
}: QuizActionButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={QUIZ_ACTION_BUTTON_CLASSES}
    >
      {children}
    </button>
  );
}

/**
 * Compact icon button used for active quiz controls.
 *
 * @param props - Control button properties.
 * @param props.title - Accessible description and browser tooltip.
 * @param props.children - Icon displayed inside the button.
 * @param props.onClick - Callback invoked when the button is selected.
 * @returns A consistently styled quiz control button.
 */
function QuizControlButton({
  title,
  children,
  onClick,
}: QuizControlButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={QUIZ_CONTROL_BUTTON_CLASSES}
    >
      {children}
    </button>
  );
}

/**
 * Icon displayed by the Skip control.
 *
 * @returns Skip icon SVG.
 */
function SkipIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 4l10 8-10 8V4z"
      />

      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19 4v16"
      />
    </svg>
  );
}

/**
 * Icon displayed by the Restart control.
 *
 * @returns Restart icon SVG.
 */
function RestartIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M20 11a8.1 8.1 0 00-15.5-2M4 5v4h4"
      />

      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4 13a8.1 8.1 0 0015.5 2M20 19v-4h-4"
      />
    </svg>
  );
}

/**
 * Icon displayed by the Stop control.
 *
 * @returns Stop icon SVG.
 */
function StopIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <rect x="6" y="6" width="12" height="12" rx="1" />
    </svg>
  );
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
              {question}
            </div>
          </div>
        )}

        {/* Inactive quiz actions */}
        {!isActive && !isFinished && (
          <div className="flex justify-center">
            {isMapReady ? (
              <div className="flex gap-2">
                {/* Start quiz */}
                <QuizActionButton onClick={onStart}>
                  Start
                </QuizActionButton>

                {/* Show or hide answer labels */}
                <QuizActionButton onClick={onToggleShowAnswers}>
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

            {/* Stop current quiz */}
            <QuizControlButton title="Stop quiz" onClick={onStop}>
              <StopIcon />
            </QuizControlButton>
          </>
        )}

        {/* Restart quiz */}
        {isActive && (
          <QuizControlButton title="Restart quiz" onClick={onRestart}>
            <RestartIcon />
          </QuizControlButton>
        )}
      </div>
    </div>
  );
}
