"use client";

import { type Quiz, useQuiz } from "./useQuiz";

type QuizControllerProps = {
  quiz: Quiz;
  children: (quizState: ReturnType<typeof useQuiz>) => React.ReactNode;
};

export default function QuizController({
  quiz,
  children,
}: QuizControllerProps) {
  const quizState = useQuiz(quiz);

  return children(quizState);
}
