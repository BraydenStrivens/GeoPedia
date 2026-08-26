/**
 * Displays the control used to restore the complete, unfiltered quiz.
 *
 * Full Quiz represents the default grouping state where every geographic
 * feature and every quiz question is available.
 */

"use client";

/**
 * Props required by the Full Quiz section.
 */
type FullQuizSectionProps = {
  /** Whether Full Quiz is currently controlling the quiz. */
  isActive: boolean;

  /** Whether grouping interactions are currently disabled. */
  isDisabled: boolean;

  /** Restores the complete unfiltered quiz. */
  onUseFullQuiz: () => void;
};

/**
 * Displays the Full Quiz grouping option.
 *
 * @param props - Full Quiz state and activation callback.
 * @returns The Full Quiz section.
 */
export default function FullQuizSection({
  isActive,
  isDisabled,
  onUseFullQuiz,
}: FullQuizSectionProps) {
  return (
    <section className="border-b border-gray-300 pb-4">
      {/* Section heading */}
      <h3 className="mb-2 text-sm font-semibold text-gray-800">
        Full Quiz
      </h3>

      {/* Full Quiz toggle */}
      <button
        type="button"
        disabled={isDisabled || isActive}
        onClick={onUseFullQuiz}
        className={[
          "w-full rounded-lg border px-3 py-2 text-sm font-semibold transition",

          isActive
            ? "border-gray-900 bg-gray-900 text-white"
            : "border-gray-300 bg-white text-gray-800 hover:bg-gray-300/80",

          isDisabled ? "cursor-not-allowed opacity-50" : "",
        ].join(" ")}
      >
        Use Full Quiz
      </button>
    </section>
  );
}
