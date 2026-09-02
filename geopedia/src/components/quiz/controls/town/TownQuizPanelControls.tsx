/**
 * Displays GeoPedia's floating Filter control and mode selector for town quizzes.
 *
 * This component owns presentation only. The town quiz client remains
 * responsible for deciding whether the Filter panel is open, whether filtering
 * may currently be changed, whether the blocked warning is visible, and how
 * Filter panel contents modify the active town set.
 *
 * The Normal / Hard selector is supplied as rendered content so town-specific
 * mode behavior remains independent from the generic floating-panel
 * presentation.
 */

"use client";

import type { ReactNode } from "react";

import QuizPanelButton from "../QuizPanelButton";

/**
 * Props required by the floating town quiz controls.
 */
type TownQuizPanelControlsProps = {
  /** Whether the Filter panel is currently open. */
  isFilterOpen: boolean;

  /** Whether the warning explaining why Filter is unavailable is visible. */
  isFilterBlockedMessageOpen: boolean;

  /** Attempts to open or close the Filter panel. */
  onToggleFilter: () => void;

  /** Closes the Filter unavailable warning. */
  onCloseFilterBlockedMessage: () => void;

  /** Rendered Filter panel content. */
  filterPanel: ReactNode;

  /** Rendered Normal / Hard town quiz mode selector. */
  modeControl: ReactNode;
};

/**
 * Displays floating town quiz controls, the Filter warning, and the currently
 * open Filter panel.
 *
 * @param props - Panel state, callbacks, and rendered town-control content.
 * @returns Floating town quiz controls.
 */
export default function TownQuizPanelControls({
  isFilterOpen,
  isFilterBlockedMessageOpen,
  onToggleFilter,
  onCloseFilterBlockedMessage,
  filterPanel,
  modeControl,
}: TownQuizPanelControlsProps) {
  return (
    <div className="absolute right-3 top-3 z-30 flex max-w-[calc(100vw-1.5rem)] flex-col items-end gap-5">
      {/* Panel and mode controls */}
      <div className="relative z-30 flex max-w-full flex-row items-start gap-5">
        {/* Normal / Hard selector */}
        {modeControl}

        {/* Filter panel toggle */}
        <QuizPanelButton
          label="Quiz filter"
          isOpen={isFilterOpen}
          onClick={onToggleFilter}
        >
          Filter
        </QuizPanelButton>

        {/* Running-quiz Filter warning */}
        {isFilterBlockedMessageOpen && (
          <div className="absolute right-0 top-12 w-56 rounded-lg border border-gray-300 bg-white p-3 text-xs text-gray-700 shadow-lg">
            <div className="flex items-start gap-2">
              {/* Warning message */}
              <p className="flex-1 leading-relaxed">
                Finish or end the current quiz before using Filter.
              </p>

              {/* Close warning */}
              <button
                type="button"
                onClick={onCloseFilterBlockedMessage}
                aria-label="Close message"
                className="shrink-0 text-sm font-bold text-gray-400 transition hover:text-gray-900"
              >
                ×
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Floating Filter panel */}
      <div className="relative z-30 flex flex-row items-start gap-5">
        {isFilterOpen && <div className="mt-2">{filterPanel}</div>}
      </div>
    </div>
  );
}
