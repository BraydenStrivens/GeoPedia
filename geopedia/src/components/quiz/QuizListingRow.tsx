import Link from "next/link";

import type { QuizListing } from "@/types/quiz";

import QuizDifficultyBadge from "./QuizDifficultyBadge";

/**
 * Properties accepted by {@link QuizListingRow}.
 */
type QuizListingRowProps = {
  /** Lightweight quiz metadata displayed in the listing. */
  quizListing: QuizListing;

  /** Route opened when the quiz listing is selected. */
  href: string;
};

/**
 * Displays a clickable quiz listing containing its name, difficulty, and
 * description.
 *
 * The entire row acts as the quiz link. Hovering anywhere over the row
 * underlines the quiz name without changing the row's background.
 *
 * @param props - Quiz listing row properties.
 * @param props.quizListing - Quiz metadata displayed by the row.
 * @param props.href - Route opened when the row is selected.
 * @returns A clickable quiz listing row.
 */
export default function QuizListingRow({
  quizListing,
  href,
}: QuizListingRowProps) {
  return (
    <Link
      href={href}
      className="
        group block w-full rounded-xl
        border border-slate-300 bg-white
        px-6 py-5 shadow-sm
        transition
        hover:-translate-y-0.5
        hover:shadow-md
        focus-visible:outline-none
        focus-visible:ring-2
        focus-visible:ring-sky-500
      "
    >
      <div className="flex items-start justify-between gap-6">
        <h3 className="text-lg font-semibold text-slate-900 group-hover:underline">
          {quizListing.name}
        </h3>

        <QuizDifficultyBadge difficulty={quizListing.difficulty} />
      </div>

      <p className="mt-2 text-sm leading-6 text-slate-600">
        {quizListing.description}
      </p>
    </Link>
  );
}
