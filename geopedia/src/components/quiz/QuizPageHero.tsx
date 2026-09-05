/**
 * Properties accepted by {@link QuizPageHero}.
 */
type QuizPageHeroProps = {
  /** Primary page title displayed prominently in the hero. */
  title: string;

  /** Supporting text displayed beneath the page title. */
  subtitle: string;
};

/**
 * Displays the shared heading used by GeoPedia quiz overview pages.
 *
 * The hero provides a consistent visual introduction for country and global
 * quiz pages while allowing each page to supply its own title and subtitle.
 *
 * @param props - Quiz page hero properties.
 * @param props.title - Primary page title.
 * @param props.subtitle - Supporting text displayed beneath the title.
 * @returns The shared quiz page hero.
 */
export default function QuizPageHero({
  title,
  subtitle,
}: QuizPageHeroProps) {
  return (
    <section
      className="
        border-b border-sky-200
        bg-gradient-to-b from-sky-100 to-sky-50
        px-6 py-12 shadow-sm
      "
    >
      <div className="mx-auto flex w-full max-w-6xl flex-col items-center text-center">
        <h1 className="text-5xl font-bold tracking-tight text-slate-950">
          {title}
        </h1>

        <p className="mt-2 max-w-2xl text-xl font-medium text-slate-500">
          {subtitle}
        </p>
      </div>
    </section>
  );
}
