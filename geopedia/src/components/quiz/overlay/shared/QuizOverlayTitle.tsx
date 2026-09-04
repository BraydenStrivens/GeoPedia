/**
 * Renders the shared title card displayed at the top of GeoPedia quiz overlays.
 *
 * Feature and town quizzes currently use the same presentation for their quiz
 * names, so the title styling is centralized here rather than duplicated
 * between the two overlay implementations.
 */

/**
 * Props required by the shared quiz overlay title.
 */
type QuizOverlayTitleProps = {
  /** User-facing name of the quiz currently displayed by the overlay. */
  quizName: string;
};

/**
 * Displays a quiz name inside the shared translucent overlay title card.
 *
 * @param props - Quiz title data.
 * @returns Shared quiz overlay title presentation.
 */
export default function QuizOverlayTitle({
  quizName,
}: QuizOverlayTitleProps) {
  return (
    <div className="rounded-lg bg-background-1/80 px-6 py-2 text-center backdrop-blur-md">
      <h1 className="text-xl font-bold leading-tight text-text">
        {quizName}
      </h1>
    </div>
  );
}
