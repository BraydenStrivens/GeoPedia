import { notFound } from "next/navigation";

import Map from "@/components/Map";
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
    console.log("FAILED TO GET QUIZ");
    console.log("COUNTRY ID: ", countryId);
    console.log("QUIZ ID: ", quizId);
    notFound();
  }

  const mapConfig = getMap(countryId, quiz.mapId);

  if (!mapConfig) {
    console.log("FAILED TO GET MAP CONFIG");
    console.log("COUNTRY ID: ", countryId);
    console.log("MAP ID: ", quiz.mapId);
    notFound();
  }

  return (
    <main className="h-[calc(100vh-3.5rem)] w-screen">
      <Map mapConfig={mapConfig} quiz={quiz} clickBehavior="quiz" />
    </main>
  );
}
