/**
 * Renders GeoPedia's Global overview page.
 *
 * The page displays quizzes covering geography that spans multiple countries
 * rather than belonging to one individual country.
 *
 * Global quiz definitions are retrieved from GeoPedia's centralized quiz
 * registry.
 */

import Link from "next/link";

import { getGlobalQuizzes } from "@/quiz/quizzes";

/**
 * Displays GeoPedia's available global geography quizzes.
 *
 * @returns The Global overview page.
 */
export default function GlobalPage() {
  const quizzes = getGlobalQuizzes();

  return (
    <main className="flex min-h-screen justify-center px-6 py-12">
      <div className="flex w-full max-w-6xl flex-col items-center">
        {/* Global heading */}
        <div className="mb-10 flex flex-col items-center text-center">
          <h1 className="text-5xl font-bold tracking-tight">
            Global
          </h1>

          <p className="mt-2 max-w-2xl text-xl font-medium text-gray-500">
            Practice geography covering countries around the world.
          </p>
        </div>

        {/* Available global quizzes */}
        <section className="w-full max-w-5xl">
          <h2 className="mb-6 text-center text-3xl font-bold">
            Quizzes
          </h2>

          {quizzes.length === 0 ? (
            /* Empty quiz state */
            <p className="text-center text-lg text-gray-500">
              Quizzes coming soon
            </p>
          ) : (
            /* Quiz links */
            <div className="flex flex-col items-center gap-3">
              {quizzes.map((quiz) => (
                <Link
                  key={quiz.id}
                  href={`/global/${quiz.id}`}
                  className="w-full max-w-xl rounded-lg border px-6 py-4 text-center font-medium shadow-sm transition hover:bg-gray-50 hover:text-black"
                >
                  {quiz.name}
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
