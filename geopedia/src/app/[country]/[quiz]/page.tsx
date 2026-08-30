/**
 * Renders an individual GeoPedia quiz page.
 *
 * The route identifies both the country and quiz. The page resolves the quiz
 * definition, finds the map configuration referenced by that quiz, and then
 * renders the client-side quiz map.
 *
 * Invalid country/quiz combinations or missing map configurations are handled
 * through Next.js 404 behavior.
 */

import { notFound } from "next/navigation";

import QuizMapClient from "@/components/quiz/QuizMapClient";
import { getCountryMap } from "@/maps/configs";
import { getCountryQuiz } from "@/quiz/quizzes";

/**
 * Dynamic route parameters supplied by Next.js for a quiz page.
 */
type QuizPageProps = {
  /** Dynamic route values identifying the country and quiz. */
  params: Promise<{
    /** GeoPedia country ID taken from the URL. */
    country: string;

    /** GeoPedia quiz ID taken from the URL. */
    quiz: string;
  }>;
};

/**
 * Displays the requested geography quiz and its associated map.
 *
 * The quiz definition determines which map configuration should be loaded.
 * Missing quizzes or map configurations are forwarded to Next.js 404 handling.
 *
 * @param props - Quiz page route properties.
 * @param props.params - Dynamic route parameters containing country and quiz IDs.
 * @returns The selected quiz page.
 */
export default async function QuizPage({ params }: QuizPageProps) {
  const { country: countryId, quiz: quizId } = await params;

  const quiz = getCountryQuiz(countryId, quizId);

  if (!quiz) {
    notFound();
  }

  const mapConfig = getCountryMap(countryId, quiz.mapId);

  if (!mapConfig) {
    notFound();
  }

  return (
    <main className="h-[calc(100vh-3.5rem)] w-screen">
      {/* Client-side interactive quiz map */}
      <QuizMapClient
        countryId={countryId}
        mapConfig={mapConfig}
        quiz={quiz}
      />
    </main>
  );
}
