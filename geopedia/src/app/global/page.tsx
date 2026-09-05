/**
 * Renders GeoPedia's Global overview page.
 *
 * The page displays quizzes covering geography that spans multiple countries
 * rather than belonging to one individual country.
 *
 * Global quiz definitions are retrieved from GeoPedia's centralized quiz
 * registry.
 */

import QuizListingRow from "@/components/quiz/QuizListingRow";
import QuizPageHero from "@/components/quiz/QuizPageHero";
import QuizSectionHeader from "@/components/quiz/QuizSectionHeader";
import { getGlobalQuizListings } from "@/quiz/quizzes";

/**
 * Displays GeoPedia's available global geography quizzes.
 *
 * @returns The Global overview page.
 */
export default function GlobalPage() {
  const quizListings = getGlobalQuizListings();

  return (
    <main className="min-h-screen bg-slate-300">
      {/* Global heading */}
      <QuizPageHero
        title="Global"
        subtitle="Practice geography covering countries around the world."
      />

      <div className="mx-auto flex w-full max-w-6xl flex-col items-center px-6 py-10">
        {/* Available global quizzes */}
        <section className="w-full max-w-5xl">
          <QuizSectionHeader description="Choose a quiz to practice global geography." />

          {quizListings.length === 0 ? (
            /* Empty quiz state */
            <p className="text-center text-lg text-slate-500">
              Quizzes coming soon
            </p>
          ) : (
            /* Quiz listings */
            <div className="mx-auto flex w-full max-w-2xl flex-col gap-3">
              {quizListings.map((quizListing) => (
                <QuizListingRow
                  key={quizListing.id}
                  quizListing={quizListing}
                  href={`/global/${quizListing.id}`}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
