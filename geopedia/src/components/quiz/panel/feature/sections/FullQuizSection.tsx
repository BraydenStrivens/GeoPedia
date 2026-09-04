/**
 * Displays controls for restoring the complete feature quiz and optionally
 * limiting it to geographic features available in GeoGuessr.
 *
 * Full Quiz represents the default grouping state where every geographic
 * feature and every quiz question is available before any optional
 * GeoGuessr-only filter is applied.
 */

"use client";

/**
 * Props required by the Full Quiz section.
 */
type FullQuizSectionProps = {
  /** Whether Full Quiz is currently controlling the feature quiz. */
  isActive: boolean;

  /** Whether GeoGuessr-only filtering is currently enabled. */
  isGeoGuessrOnly: boolean;

  /** Whether this feature quiz supports GeoGuessr-only filtering. */
  supportsGeoGuessrFilter: boolean;

  /** Restores the complete ungrouped feature quiz. */
  onUseFullQuiz: () => void;

  /** Enables or disables GeoGuessr-only filtering. */
  onGeoGuessrOnlyChange: (isEnabled: boolean) => void;
};

/**
 * Displays the Full Quiz grouping option and optional GeoGuessr filter.
 *
 * @param props - Full Quiz section properties.
 * @param props.isActive - Whether Full Quiz is currently active.
 * @param props.isGeoGuessrOnly - Whether GeoGuessr-only filtering is enabled.
 * @param props.supportsGeoGuessrFilter - Whether the current map data supports
 * GeoGuessr filtering.
 * @param props.onUseFullQuiz - Callback for restoring the complete quiz.
 * @param props.onGeoGuessrOnlyChange - Callback for changing the GeoGuessr
 * filter.
 * @returns The Full Quiz section.
 */
export default function FullQuizSection({
  isActive,
  isGeoGuessrOnly,
  supportsGeoGuessrFilter,
  onUseFullQuiz,
  onGeoGuessrOnlyChange,
}: FullQuizSectionProps) {
  return (
    <section className="border-b border-border pb-4">
      {/* Section heading */}
      <h3 className="mb-2 text-sm font-semibold text-text">
        Full Quiz
      </h3>

      {/* Full Quiz selection */}
      <button
        type="button"
        disabled={isActive}
        onClick={onUseFullQuiz}
        aria-pressed={isActive}
        className={[
          "w-full rounded-lg border px-3 py-2",
          "text-sm font-semibold transition",
          isActive
            ? "cursor-default border-selected-control bg-selected-control text-button-text"
            : "border-border bg-background-1 text-text hover:bg-background-3",
        ].join(" ")}
      >
        Use Full Quiz
      </button>

      {supportsGeoGuessrFilter && (
        /* Optional GeoGuessr eligibility filter */
        <div className="flex w-full items-center justify-end py-2">
          <label className="flex cursor-pointer items-center gap-2 text-sm font-medium">
            <span className="text-text-secondary">
              GeoGuessr Only
            </span>

            <input
              type="checkbox"
              checked={isGeoGuessrOnly}
              onChange={(event) =>
                onGeoGuessrOnlyChange(event.target.checked)
              }
              className="h-4 w-4 cursor-pointer"
            />
          </label>
        </div>
      )}
    </section>
  );
}
