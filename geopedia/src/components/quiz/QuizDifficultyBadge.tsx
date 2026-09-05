import type { QuizDifficulty } from "@/types/quiz";

/**
 * Properties accepted by {@link QuizDifficultyBadge}.
 */
type QuizDifficultyBadgeProps = {
  /** Difficulty tier displayed by the badge. */
  difficulty: QuizDifficulty;
};

/**
 * Presentation settings associated with each quiz difficulty tier.
 */
const DIFFICULTY_STYLES: Record<
  QuizDifficulty,
  {
    label: string;
    className: string;
  }
> = {
  easy: {
    label: "Easy",
    className: "bg-emerald-300 text-emerald-950",
  },
  medium: {
    label: "Medium",
    className: "bg-orange-300 text-orange-950",
  },
  hard: {
    label: "Hard",
    className: "bg-red-300 text-red-950",
  },
  extreme: {
    label: "Extreme",
    className: "bg-red-950 text-white",
  },
};

/**
 * Displays a compact color-coded badge representing a quiz's difficulty.
 *
 * Difficulty is derived before reaching this component, allowing the badge to
 * remain purely presentational.
 *
 * @param props - Difficulty badge properties.
 * @param props.difficulty - Difficulty tier to display.
 * @returns A color-coded quiz difficulty badge.
 */
export default function QuizDifficultyBadge({
  difficulty,
}: QuizDifficultyBadgeProps) {
  const difficultyStyle = DIFFICULTY_STYLES[difficulty];

  return (
    <span
      className={`
        shrink-0 rounded-md px-3 py-1 text-xs font-semibold
        ${difficultyStyle.className}
      `}
    >
      {difficultyStyle.label}
    </span>
  );
}
