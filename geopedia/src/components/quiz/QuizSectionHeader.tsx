/**
 * Properties accepted by {@link QuizSectionHeader}.
 */
type QuizSectionHeaderProps = {
  /** Supporting text displayed beneath the Quizzes heading. */
  description: string;
};

/**
 * Displays the shared heading for a page's available quiz listings.
 *
 * The heading and supporting description remain centered to match the visual
 * alignment used throughout GeoPedia's quiz overview pages.
 *
 * @param props - Quiz section header properties.
 * @param props.description - Supporting description shown beneath the heading.
 * @returns The shared quiz section heading.
 */
export default function QuizSectionHeader({
  description,
}: QuizSectionHeaderProps) {
  return (
    <div className="mb-6 border-b border-slate-400 pb-3 text-center">
      <h2 className="text-3xl font-bold text-slate-950">Quizzes</h2>

      <p className="mt-1 text-sm text-slate-600">{description}</p>
    </div>
  );
}
