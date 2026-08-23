/**
 * Provides the state and behavior required to run a GeoPedia quiz.
 *
 * This hook owns the state for one quiz attempt, including:
 *
 * - Randomized question order
 * - Current-question tracking
 * - Answer validation results
 * - Correct and incorrect counts
 * - Completed-answer statuses
 * - Hard Mode's most recent visible result
 * - Question skipping
 * - Recycled missed answers
 * - Restarting and stopping
 * - Quiz completion state
 */

import { useEffect, useRef, useState } from "react";

import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";

/**
 * Optional behavior that changes how a quiz attempt is processed.
 */
type UseQuizOptions = {
  /** Returns incorrectly answered questions to the end of the queue. */
  recycleMissedAnswers?: boolean;
};

/**
 * Creates a randomized copy of a quiz question array using Fisher-Yates.
 *
 * The original questions array is never modified.
 *
 * @param questions - Questions to randomize.
 * @returns A new array containing the same questions in randomized order.
 */
function shuffleQuestions(questions: QuizQuestion[]): QuizQuestion[] {
  const shuffledQuestions = [...questions];

  for (
    let currentIndex = shuffledQuestions.length - 1;
    currentIndex > 0;
    currentIndex--
  ) {
    const randomIndex = Math.floor(
      Math.random() * (currentIndex + 1),
    );

    [
      shuffledQuestions[currentIndex],
      shuffledQuestions[randomIndex],
    ] = [
      shuffledQuestions[randomIndex],
      shuffledQuestions[currentIndex],
    ];
  }

  return shuffledQuestions;
}

/**
 * Moves the first question in a queue to the end.
 *
 * Queues containing zero or one question are returned unchanged because
 * moving the first question would have no effect.
 *
 * @param questionQueue - Current ordered question queue.
 * @returns A new queue with the first question moved to the end.
 */
function moveCurrentQuestionToEnd(
  questionQueue: QuizQuestion[],
): QuizQuestion[] {
  if (questionQueue.length <= 1) {
    return questionQueue;
  }

  return [...questionQueue.slice(1), questionQueue[0]];
}

/**
 * Manages the complete state and behavior of one quiz attempt.
 *
 * @param quiz - Quiz definition containing the questions to run.
 * @param options - Optional behavior that changes how answers are processed.
 * @returns Current quiz state and functions for answering, skipping,
 * restarting, and stopping the quiz.
 */
export function useQuiz(quiz: Quiz, options: UseQuizOptions = {}) {
  const { recycleMissedAnswers = false } = options;

  /**
   * Ordered questions remaining in the current attempt.
   *
   * The first question is always the current question.
   */
  const [questionQueue, setQuestionQueue] = useState<QuizQuestion[]>(
    () => shuffleQuestions(quiz.questions),
  );

  /**
   * Completion result for each answer keyed by the answer value.
   *
   * Answers do not appear here until they have been completed. Recycled
   * incorrect answers therefore remain absent until eventually completed.
   */
  const [answerStatuses, setAnswerStatuses] = useState<
    Record<string, AnswerStatus>
  >({});

  /**
   * Answer whose result should currently remain visible in Hard Mode.
   *
   * This is cleared when the question queue advances without completing an
   * answer, such as when a question is skipped or recycled after a miss.
   */
  const [lastAnsweredAnswer, setLastAnsweredAnswer] = useState<
    string | undefined
  >(undefined);

  /** Number of completed questions in the current attempt. */
  const [answeredCount, setAnsweredCount] = useState(0);

  /** Number of correct selections made during the current attempt. */
  const [correctCount, setCorrectCount] = useState(0);

  /** Number of incorrect selections made during the current attempt. */
  const [wrongCount, setWrongCount] = useState(0);

  /** Determines whether the quiz is currently accepting answers. */
  const [isActive, setIsActive] = useState(false);

  /** The first queued question is always the question currently being asked. */
  const currentQuestion = questionQueue[0];

  /**
   * Keeps the current question available to event handlers created during an
   * earlier render.
   *
   * MapLibre click handlers can remain alive across React renders, so they
   * need a mutable ref instead of capturing an outdated currentQuestion.
   */
  const currentQuestionRef = useRef(currentQuestion);

  /**
   * Synchronizes currentQuestionRef whenever the queue changes.
   */
  useEffect(() => {
    currentQuestionRef.current = currentQuestion;
  }, [currentQuestion]);

  /**
   * Records the result of the current question and advances the queue.
   *
   * Correct answers are always completed immediately.
   *
   * Incorrect answers either:
   *
   * - Complete normally and receive a `wrong` status, or
   * - Return to the end of the queue when Recycle Missed Answers is enabled.
   *
   * @param isCorrect - Whether the selected geographic feature was correct.
   */
  function answerQuestion(isCorrect: boolean): void {
    const question = currentQuestionRef.current;

    if (!question || !isActive) {
      return;
    }

    const currentAnswer = question.answer;

    if (isCorrect) {
      setAnswerStatuses((previousStatuses) => ({
        ...previousStatuses,

        [currentAnswer]: "correct",
      }));

      setLastAnsweredAnswer(currentAnswer);

      setCorrectCount((previousCount) => previousCount + 1);

      setAnsweredCount((previousCount) => previousCount + 1);

      setQuestionQueue((previousQueue) => previousQueue.slice(1));

      return;
    }

    setWrongCount((previousCount) => previousCount + 1);

    if (recycleMissedAnswers) {
      /*
       * A recycled miss advances the queue without completing the answer.
       * Clear the previous Hard Mode result so an older feature does not
       * remain highlighted after the question changes.
       */
      setLastAnsweredAnswer(undefined);

      setQuestionQueue(moveCurrentQuestionToEnd);

      return;
    }

    setAnswerStatuses((previousStatuses) => ({
      ...previousStatuses,

      [currentAnswer]: "wrong",
    }));

    setLastAnsweredAnswer(currentAnswer);

    setAnsweredCount((previousCount) => previousCount + 1);

    setQuestionQueue((previousQueue) => previousQueue.slice(1));
  }

  /**
   * Moves the current question to the end of the queue without changing
   * scores or answer statuses.
   *
   * Skipping also clears Hard Mode's previous visible result because the
   * question changed without producing a new completed answer.
   */
  function skipQuestion(): void {
    if (!currentQuestionRef.current || !isActive) {
      return;
    }

    setLastAnsweredAnswer(undefined);

    setQuestionQueue(moveCurrentQuestionToEnd);
  }

  /**
   * Clears all attempt state and starts a new randomized quiz.
   */
  function restartQuiz(): void {
    setQuestionQueue(shuffleQuestions(quiz.questions));

    setAnswerStatuses({});

    setLastAnsweredAnswer(undefined);

    setAnsweredCount(0);
    setCorrectCount(0);
    setWrongCount(0);

    setIsActive(true);
  }

  /**
   * Stops the current quiz and clears all attempt state.
   */
  function stopQuiz(): void {
    setQuestionQueue([]);

    setAnswerStatuses({});

    setLastAnsweredAnswer(undefined);

    setAnsweredCount(0);
    setCorrectCount(0);
    setWrongCount(0);

    setIsActive(false);
  }

  const questionCount = quiz.questions.length;

  const isFinished = isActive && questionQueue.length === 0;

  return {
    currentQuestion,

    answerQuestion,
    skipQuestion,
    restartQuiz,
    stopQuiz,

    answerStatuses,
    lastAnsweredAnswer,

    answeredCount,
    questionCount,
    correctCount,
    wrongCount,

    isActive,
    isFinished,
  };
}
