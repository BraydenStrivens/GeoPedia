/**
 * Renders an individual GeoPedia global quiz page.
 *
 * The route identifies the requested global quiz. The page resolves the quiz
 * definition, finds the map configuration referenced by that quiz, and then
 * renders the client-side quiz map.
 *
 * Invalid quiz IDs or missing map configurations are handled through Next.js
 * 404 behavior.
 */

import { notFound } from "next/navigation";

import QuizMapClient from "@/components/quiz/QuizMapClient";
import { getGlobalMap } from "@/maps/configs";
import { getGlobalQuiz } from "@/quiz/quizzes";

/**
 * Dynamic route parameters supplied by Next.js for a global quiz page.
 */
type GlobalQuizPageProps = {
  /** Dynamic route values identifying the global quiz. */
  params: Promise<{
    /** GeoPedia global quiz ID taken from the URL. */
    quiz: string;
  }>;
};

/**
 * Displays the requested global geography quiz and its associated map.
 *
 * The quiz definition determines which global map configuration should be
 * loaded. Missing quizzes or map configurations are forwarded to Next.js 404
 * handling.
 *
 * @param props - Global quiz page route properties.
 * @param props.params - Dynamic route parameters containing the quiz ID.
 * @returns The selected global quiz page.
 */
export default async function GlobalQuizPage({
  params,
}: GlobalQuizPageProps) {
  const { quiz: quizId } = await params;

  const quiz = getGlobalQuiz(quizId);

  if (!quiz) {
    notFound();
  }

  const mapConfig = getGlobalMap(quiz.mapId);

  if (!mapConfig) {
    notFound();
  }

  return (
    <main className="h-[calc(100vh-3.5rem)] w-screen">
      {/* Client-side interactive quiz map */}
      <QuizMapClient
        kind={"feature"}
        countryId="global"
        mapConfig={mapConfig}
        quiz={quiz}
      />
    </main>
  );
}
