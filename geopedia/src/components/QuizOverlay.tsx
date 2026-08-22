/**
 * Renders the floating quiz interface displayed above an active map.
 *
 * The overlay presents the quiz name, progress, score, current question,
 * completion state, and controls for starting, skipping, stopping, and
 * restarting a quiz.
 *
 * QuizOverlay does not manage quiz state itself. Instead, it receives the
 * current quiz state and control functions through props from the component
 * using the useQuiz hook.
 */

"use client";

/**
 * Values and event handlers required to render and control the quiz overlay.
 */
type QuizOverlayProps = {
  quizName: string;
  question: string;

  answeredCount: number;
  questionCount: number;
  correctCount: number;
  wrongCount: number;

  isActive: boolean;
  isFinished: boolean;
  isMapReady: boolean;

  onSkip: () => void;
  onRestart: () => void;
  onStop: () => void;
};

/**
 * Icon displayed by the Skip button.
 */
function SkipIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="h-4 w-4"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 4l10 8-10 8V4z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 4v16" />
    </svg>
  );
}

/**
 * Icon displayed by the Restart button.
 */
function RestartIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="h-4 w-4"
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
 * Icon displayed by the Stop button.
 */
function StopIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
      <rect x="6" y="6" width="12" height="12" rx="1" />
    </svg>
  );
}

/**
 * Displays the current quiz status and available quiz controls.
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
  onSkip,
  onRestart,
  onStop,
}: QuizOverlayProps) {
  return (
    <div className="pointer-events-none absolute inset-x-0 top-3 z-10 flex flex-col items-center">
      {/* Main information box */}
      <div className="pointer-events-auto rounded-xl bg-black/20 p-2 backdrop-blur-sm min-w-[220px]">
        {/* Title */}
        <div className="rounded-lg bg-white/80 px-6 py-2 text-center backdrop-blur-md">
          <h1 className="text-xl font-bold leading-tight text-gray-900">
            {quizName}
          </h1>
        </div>

        {/* Progress */}
        <div className="flex items-center justify-between px-2">
          {/* Correct Count */}
          <div className="flex items-center gap-1 text-sm font-semibold">
            <span>{correctCount}</span>
            <span className="text-green-600">✓</span>
          </div>
          {/* Progress */}
          <div className="text-center text-sm font-semibold text-gray-700">
            {answeredCount} / {questionCount}
          </div>
          {/* Wrong Count*/}
          <div className="flex items-center gap-1 text-sm font-semibold">
            <span className="text-red-600">✕</span>
            <span>{wrongCount}</span>
          </div>
        </div>

        {/* Question */}
        {isActive && !isFinished && (
          <div className="rounded-lg bg-white/80 px-5 py-1.5 text-center backdrop-blur-md">
            <div className="text-lg font-bold leading-tight text-gray-900">
              {question}
            </div>
          </div>
        )}

        {/* Initial 'Start' Button */}
        {/* {!isActive && !isFinished && (
          <div className="flex justify-center">
            <button
              type="button"
              onClick={onRestart}
              title="Start"
              className="rounded-lg bg-white/80 px-5 py-1.5 text-center backdrop-blur-md text-xl font-bold leading-tight text-gray-900 hover:bg-white/60 hover:text-gray-600"
            >
              Start
            </button>
          </div>
        )} */}
        {!isActive && !isFinished && (
          <div className="flex justify-center">
            {isMapReady ? (
              <button
                type="button"
                onClick={onRestart}
                title="Start"
                className="rounded-lg bg-white/80 px-5 py-1.5 text-center text-xl font-bold leading-tight text-gray-900 backdrop-blur-md hover:bg-white/60 hover:text-gray-600"
              >
                Start
              </button>
            ) : (
              <div
                className="flex items-center justify-center rounded-lg bg-white/80 px-5 py-2 backdrop-blur-md"
                aria-label="Loading map"
              >
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900" />
              </div>
            )}
          </div>
        )}

        {/* Finished */}
        {isFinished && (
          <div className="rounded-lg bg-white/80 px-5 py-2 text-center backdrop-blur-md">
            <div className="text-base font-bold text-gray-900">
              Quiz Complete!
            </div>

            <div className="text-xs text-gray-500">
              {correctCount} correct out of {questionCount}
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="mt-1 flex justify-center gap-1">
        {isActive && !isFinished && (
          <>
            <button
              type="button"
              onClick={onSkip}
              title="Skip question"
              className="pointer-events-auto flex h-6 w-6 items-center justify-center rounded-md bg-white/80 text-gray-600 shadow-sm backdrop-blur-sm transition hover:bg-white hover:text-gray-900 active:scale-90"
            >
              <SkipIcon />
            </button>

            <button
              type="button"
              onClick={onStop}
              title="Stop quiz"
              className="pointer-events-auto flex h-6 w-6 items-center justify-center rounded-md bg-white/80 text-gray-600 shadow-sm backdrop-blur-sm transition hover:bg-white hover:text-gray-900 active:scale-90"
            >
              <StopIcon />
            </button>
          </>
        )}

        {isActive && (
          <button
            type="button"
            onClick={onRestart}
            title="Restart quiz"
            className="pointer-events-auto flex h-6 w-6 items-center justify-center rounded-md bg-white/80 text-gray-600 shadow-sm backdrop-blur-sm transition hover:bg-white hover:text-gray-900 active:scale-90"
          >
            <RestartIcon />
          </button>
        )}
      </div>
    </div>
  );
}
