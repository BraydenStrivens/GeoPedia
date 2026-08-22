/**
 * Adapts quiz state from the map's quiz system for display by QuizOverlay.
 *
 * This component acts as a small bridge between map quiz state and the
 * presentation-focused QuizOverlay component. It forwards quiz progress,
 * score, state, and control callbacks while providing a fallback value when
 * there is no current question.
 */

"use client";

import QuizOverlay from "./QuizOverlay";

/**
 * Quiz state and controls required to display the overlay on a quiz map.
 */
type QuizMapOverlayProps = {
  quizName: string;
  currentQuestion: string | undefined;

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
 * Converts map quiz state into the props expected by QuizOverlay.
 */
export default function QuizMapOverlay({
  quizName,
  currentQuestion,
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
}: QuizMapOverlayProps) {
  return (
    <QuizOverlay
      quizName={quizName}
      question={currentQuestion ?? "Finished!"}
      answeredCount={answeredCount}
      questionCount={questionCount}
      correctCount={correctCount}
      wrongCount={wrongCount}
      isActive={isActive}
      isFinished={isFinished}
      isMapReady={isMapReady}
      onSkip={onSkip}
      onRestart={onRestart}
      onStop={onStop}
    />
  );
}
