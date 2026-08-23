import { notFound } from "next/navigation";

import QuizMapClient from "@/components/quiz/QuizMapClient";
import { getMap } from "@/maps";
import { getQuiz } from "@/quiz/quizzes";

type QuizPageProps = {
  params: Promise<{
    country: string;
    quiz: string;
  }>;
};

export default async function QuizPage({ params }: QuizPageProps) {
  const { country: countryId, quiz: quizId } = await params;

  const quiz = getQuiz(countryId, quizId);

  if (!quiz) {
    notFound();
  }

  const mapConfig = getMap(countryId, quiz.mapId);

  if (!mapConfig) {
    notFound();
  }

  return (
    <main className="h-[calc(100vh-3.5rem)] w-screen">
      <QuizMapClient
        countryId={countryId}
        mapConfig={mapConfig}
        quiz={quiz}
      />
    </main>
  );
}
