/**
 * Owns the runtime state and gameplay lifecycle of a GeoPedia town quiz.
 *
 * Town quizzes ask the user to place named towns on the map by clicking an
 * arbitrary geographic coordinate. This hook manages question order, quiz
 * progress, score accumulation, cumulative geographic error, the most recent
 * guess result, and quiz lifecycle controls.
 *
 * Submitted guesses immediately advance to the next question. The most recent
 * result remains available after advancing so the map can continue displaying
 * the previous guess-to-target visualization while the user considers the next
 * town.
 *
 * Skipping differs from answering: the current unanswered town is moved to the
 * end of the remaining question queue without changing score, distance totals,
 * or answered-question progress.
 */

"use client";

import { useCallback, useState } from "react";

import {
  type GeographicCoordinate,
  getGeographicDistanceKm,
  getTownGuessScore,
} from "@/quiz/town/townScoring";
import type { TownQuizTown } from "@/types/quiz";

/**
 * Result produced by one submitted town guess.
 */
export type TownQuizGuessResult = {
  /** Town that was being answered. */
  town: TownQuizTown;

  /** Geographic location selected by the user. */
  guess: GeographicCoordinate;

  /** Distance between the guess and target town. */
  distanceKm: number;

  /** Normalized score from 0 through 1. */
  score: number;
};

/**
 * Configuration required by the town quiz runtime.
 */
type UseTownQuizParams = {
  /** Towns available to the current quiz attempt. */
  towns: TownQuizTown[];

  /** Geographic error distance at which a guess receives zero points. */
  maxErrorKm: number;
};

/**
 * Runtime state and actions exposed by the town quiz engine.
 */
type UseTownQuizResult = {
  /** Town currently being located by the user. */
  currentQuestion: TownQuizTown | undefined;

  /**
   * Result from the most recently submitted guess.
   *
   * The result remains available while the following question is active so the
   * map can continue displaying geographic result feedback.
   */
  lastResult: TownQuizGuessResult | undefined;

  /** Number of questions answered during the current attempt. */
  answeredCount: number;

  /** Total number of questions belonging to the current attempt. */
  questionCount: number;

  /** Sum of normalized scores earned during the current attempt. */
  totalScore: number;

  /** Average normalized score across all answered questions. */
  averageScore: number;

  /** Sum of geographic error across all answered questions, in kilometers. */
  totalDistanceKm: number;

  /** Whether the quiz currently has an unanswered active question. */
  isActive: boolean;

  /** Whether every question in the current attempt has been answered. */
  isFinished: boolean;

  /** Starts a new randomized quiz attempt. */
  startQuiz: () => void;

  /** Moves the current unanswered question to the end of the remaining queue. */
  skipQuestion: () => void;

  /** Stops the current attempt and returns to the inactive quiz state. */
  stopQuiz: () => void;

  /** Immediately starts a new randomized attempt. */
  restartQuiz: () => void;

  /** Scores a geographic guess for the current town. */
  submitGuess: (guess: GeographicCoordinate) => void;
};

/**
 * Randomizes question order using a Fisher-Yates shuffle.
 *
 * @param towns - Towns to randomize.
 * @returns New array containing the towns in randomized order.
 */
function shuffleTowns(towns: TownQuizTown[]): TownQuizTown[] {
  const shuffled = [...towns];

  for (let index = shuffled.length - 1; index > 0; index--) {
    const randomIndex = Math.floor(Math.random() * (index + 1));

    [shuffled[index], shuffled[randomIndex]] = [
      shuffled[randomIndex],
      shuffled[index],
    ];
  }

  return shuffled;
}

/**
 * Manages one town quiz attempt.
 *
 * @param params - Town questions and country-specific scoring configuration.
 * @returns Current town quiz state and gameplay actions.
 */
export function useTownQuiz({
  towns,
  maxErrorKm,
}: UseTownQuizParams): UseTownQuizResult {
  /**
   * Randomized town order for the current attempt.
   *
   * Questions before `currentQuestionIndex` have already been answered. The
   * question at the current index and every question after it remain unanswered.
   */
  const [questionQueue, setQuestionQueue] = useState<TownQuizTown[]>(
    [],
  );

  /** Index of the currently active unanswered town. */
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  /** Most recently completed geographic guess. */
  const [lastResult, setLastResult] = useState<
    TownQuizGuessResult | undefined
  >(undefined);

  /** Sum of normalized scores earned during the attempt. */
  const [totalScore, setTotalScore] = useState(0);

  /** Sum of geographic error accumulated during the attempt. */
  const [totalDistanceKm, setTotalDistanceKm] = useState(0);

  /** Whether a question is currently accepting guesses. */
  const [isActive, setIsActive] = useState(false);

  /**
   * Town currently being located.
   *
   * Finished and inactive quizzes intentionally expose no current question.
   */
  const currentQuestion = isActive
    ? questionQueue[currentQuestionIndex]
    : undefined;

  /**
   * Whether every question in the current attempt has been answered.
   *
   * A finished quiz retains its completed question queue and advances the
   * question index one position beyond the final question.
   */
  const isFinished =
    questionQueue.length > 0 &&
    !isActive &&
    currentQuestionIndex >= questionQueue.length;

  /**
   * Number of completed questions.
   *
   * Because skipped towns remain inside the unanswered portion of the queue,
   * this index also accurately represents answered-question progress.
   */
  const answeredCount = Math.min(
    currentQuestionIndex,
    questionQueue.length,
  );

  /**
   * Total number of questions in the current attempt.
   *
   * Before an attempt begins, the source town count is used so the inactive UI
   * can still display the eventual quiz size if needed.
   */
  const questionCount =
    questionQueue.length > 0 ? questionQueue.length : towns.length;

  /** Average score across completed guesses. */
  /** Average normalized score across completed guesses. */
  const averageScore =
    answeredCount === 0 ? 0 : totalScore / answeredCount;

  /**
   * Resets attempt statistics and begins a newly randomized quiz.
   */
  const startQuiz = useCallback(() => {
    setQuestionQueue(shuffleTowns(towns));
    setCurrentQuestionIndex(0);
    setLastResult(undefined);
    setTotalScore(0);
    setTotalDistanceKm(0);
    setIsActive(towns.length > 0);
  }, [towns]);

  /**
   * Moves the current unanswered question to the end of the remaining queue.
   *
   * Already answered questions remain fixed at the beginning of the queue.
   * Skipping does not count as an answer and therefore does not change score,
   * distance totals, progress, or the previous guess result.
   *
   * When only one unanswered question remains there is nowhere meaningful to
   * move it, so skipping becomes a no-op.
   */
  const skipQuestion = useCallback(() => {
    if (!isActive) {
      return;
    }

    setQuestionQueue((previousQueue) => {
      const remainingQuestionCount =
        previousQueue.length - currentQuestionIndex;

      if (remainingQuestionCount <= 1) {
        return previousQueue;
      }

      const answeredQuestions = previousQueue.slice(
        0,
        currentQuestionIndex,
      );

      const currentQuestion = previousQueue[currentQuestionIndex];

      const remainingQuestions = previousQueue.slice(
        currentQuestionIndex + 1,
      );

      if (!currentQuestion) {
        return previousQueue;
      }

      return [
        ...answeredQuestions,
        ...remainingQuestions,
        currentQuestion,
      ];
    });
  }, [isActive, currentQuestionIndex]);

  /**
   * Stops the current quiz without producing a completion result.
   *
   * Returning to the inactive state clears all attempt-specific progress and
   * result data.
   */
  const stopQuiz = useCallback(() => {
    setIsActive(false);
    setQuestionQueue([]);
    setCurrentQuestionIndex(0);
    setLastResult(undefined);
    setTotalScore(0);
    setTotalDistanceKm(0);
  }, []);

  /**
   * Immediately starts a new randomized attempt.
   */
  const restartQuiz = startQuiz;

  /**
   * Scores a geographic guess and immediately advances to the next question.
   *
   * Score and geographic error are accumulated independently. The completed
   * result remains stored in `lastResult`, allowing the map to display the
   * previous guess while the next town is already active.
   *
   * Finishing the final question leaves the result and aggregate statistics
   * available for the completed-quiz summary.
   */
  const submitGuess = useCallback(
    (guess: GeographicCoordinate): void => {
      if (!isActive) {
        return;
      }

      const town = questionQueue[currentQuestionIndex];

      if (!town) {
        return;
      }

      const distanceKm = getGeographicDistanceKm(guess, {
        latitude: town.latitude,
        longitude: town.longitude,
      });

      const score = getTownGuessScore(distanceKm, maxErrorKm);

      setLastResult({
        town,
        guess,
        distanceKm,
        score,
      });

      setTotalScore((previousScore) => previousScore + score);

      setTotalDistanceKm(
        (previousDistance) => previousDistance + distanceKm,
      );

      const nextQuestionIndex = currentQuestionIndex + 1;

      if (nextQuestionIndex >= questionQueue.length) {
        setCurrentQuestionIndex(nextQuestionIndex);
        setIsActive(false);

        return;
      }

      setCurrentQuestionIndex(nextQuestionIndex);
    },
    [isActive, questionQueue, currentQuestionIndex, maxErrorKm],
  );

  return {
    currentQuestion,
    lastResult,

    answeredCount,
    questionCount,

    totalScore,
    averageScore,
    totalDistanceKm,

    isActive,
    isFinished,

    startQuiz,
    skipQuestion,
    stopQuiz,
    restartQuiz,

    submitGuess,
  };
}
