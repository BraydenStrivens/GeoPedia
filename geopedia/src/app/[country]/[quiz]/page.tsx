/**
 * Renders an individual country quiz page.
 *
 * Country quiz routes support both feature-based and town-based quizzes.
 * Feature quizzes resolve their geographic `MapConfig` from the map registry,
 * while town quizzes resolve the country-specific camera and scoring values
 * required by the generic town quiz system.
 *
 * This server component validates the requested country, quiz, and required
 * configuration before passing the resolved data to the shared client-side
 * quiz map boundary.
 */

import { notFound } from "next/navigation";

import QuizMapClient from "@/components/quiz/QuizMapClient";
import { getCountry } from "@/countries";
import { getCountryMap } from "@/maps/configs";
import { getCountryQuiz } from "@/quiz/quizzes";
import { getTownCountryConfig } from "@/quiz/town/townCountryConfigs";

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

  const country = getCountry(countryId);

  if (!country) {
    return;
  }

  console.log("COUNTRY ID: ", countryId);
  console.log("COUNTRY NAME: ", country.name);
  console.log("QUIZ ID: ", quizId);

  const quiz = await getCountryQuiz(countryId, quizId, country.name);

  console.log("QUIZ: ", quiz);

  if (!quiz) {
    notFound();
  }

  if (quiz.kind === "town") {
    const townConfig = getTownCountryConfig(countryId);

    if (!townConfig) {
      notFound();
    }

    return (
      <main className="h-[calc(100vh-3.5rem)] w-screen">
        <QuizMapClient
          kind="town"
          countryId={countryId}
          quiz={quiz}
          townConfig={townConfig}
        />
      </main>
    );
  }

  const mapConfig = getCountryMap(countryId, quiz.mapId);

  if (!mapConfig) {
    notFound();
  }

  return (
    <main className="h-[calc(100vh-3.5rem)] w-screen">
      <QuizMapClient
        kind="feature"
        countryId={countryId}
        quiz={quiz}
        mapConfig={mapConfig}
      />
    </main>
  );
}
