/**
 * Provides the state and behavior required to run a GeoPedia quiz.
 *
 * The useQuiz custom hook manages the quiz's randomized question queue,
 * answer validation, scoring, answer statuses, skipping, restarting,
 * stopping, and completion state. Components can use this hook without
 * needing to implement the underlying quiz state management themselves.
 */

import { useEffect, useRef, useState } from "react";

import type { AnswerStatus, Quiz, QuizQuestion } from "@/types/quiz";

type UseQuizOptions = {
  recycleMissedAnswers?: boolean;
};

/**
 * Creates a randomized copy of a quiz's questions using the
 * Fisher-Yates shuffle algorithm.
 *
 * The original questions array is not modified.
 */
function shuffleQuestions(questions: QuizQuestion[]): QuizQuestion[] {
  const shuffled = [...questions];

  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));

    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }

  return shuffled;
}

/**
 * Manages the state and behavior of a quiz.
 *
 * Handles question order, answer validation, answer statuses,
 * scoring, skipping, restarting, stopping, and quiz completion.
 */
export function useQuiz(quiz: Quiz, options: UseQuizOptions = {}) {
  const { recycleMissedAnswers = false } = options;

  // Questions remaining in the quiz, initially shuffled.
  const [questionQueue, setQuestionQueue] = useState<QuizQuestion[]>(() =>
    shuffleQuestions(quiz.questions),
  );

  // Stores the result of each answered question by its answer value.
  const [answerStatuses, setAnswerStatuses] = useState<
    Record<string, AnswerStatus>
  >({});

  // Stores the last answered question. Used in "Hard-Mode" to only shade the last answered question.
  const [lastAnsweredAnswer, setLastAnsweredAnswer] = useState<
    string | undefined
  >(undefined);

  const [answeredCount, setAnsweredCount] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [wrongCount, setWrongCount] = useState(0);

  // Determines whether the quiz is currently accepting answers.
  const [isActive, setIsActive] = useState(false);

  // The first question in the queue is always the current question.
  const currentQuestion = questionQueue[0];

  /**
   * Keeps a mutable reference to the latest current question.
   * This allows external event handlers to access the current value
   * without depending on the render in which the handler was created.
   */
  const currentQuestionRef = useRef(currentQuestion);

  useEffect(() => {
    currentQuestionRef.current = currentQuestion;
  }, [currentQuestion]);

  /**
   * Updates a clicked feature when the user answers a question,
   * records the result, updates the score, and advances the queue.
   */
  function answerQuestion(isCorrect: boolean) {
    const question = currentQuestionRef.current;

    if (!question || !isActive) {
      return;
    }

    const answer = question.answer;

    if (isCorrect) {
      setAnswerStatuses((previousStatuses) => ({
        ...previousStatuses,
        [answer]: "correct",
      }));

      setLastAnsweredAnswer(answer);

      setCorrectCount((previousCount) => previousCount + 1);

      setAnsweredCount((previousCount) => previousCount + 1);

      setQuestionQueue((previousQueue) => previousQueue.slice(1));

      return;
    }

    setWrongCount((previousCount) => previousCount + 1);

    if (recycleMissedAnswers) {
      setQuestionQueue((previousQueue) => {
        if (previousQueue.length <= 1) {
          return previousQueue;
        }

        return [...previousQueue.slice(1), previousQueue[0]];
      });

      return;
    }

    setAnswerStatuses((previousStatuses) => ({
      ...previousStatuses,
      [answer]: "wrong",
    }));

    setLastAnsweredAnswer(answer);

    setAnsweredCount((previousCount) => previousCount + 1);

    setQuestionQueue((previousQueue) => previousQueue.slice(1));
  }

  function skipQuestion() {
    if (!currentQuestionRef.current || !isActive) {
      return;
    }

    setQuestionQueue((previousQueue) => {
      if (previousQueue.length <= 1) {
        return previousQueue;
      }

      return [...previousQueue.slice(1), previousQueue[0]];
    });
  }

  /**
   * Resets all quiz state and starts a new randomized attempt.
   */
  function restartQuiz() {
    setQuestionQueue(shuffleQuestions(quiz.questions));
    setAnswerStatuses({});
    setLastAnsweredAnswer(undefined);
    setIsActive(true);
    setAnsweredCount(0);
    setCorrectCount(0);
    setWrongCount(0);
  }

  /**
   * Stops the current quiz and clears its active state and results.
   */
  function stopQuiz() {
    setQuestionQueue([]);
    setAnswerStatuses({});
    setLastAnsweredAnswer(undefined);
    setIsActive(false);
    setAnsweredCount(0);
    setCorrectCount(0);
    setWrongCount(0);
  }

  const questionCount = quiz.questions.length;

  // A quiz is finished only after it has been started and its queue is empty.
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
