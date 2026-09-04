/**
 * Displays the floating auxiliary panel controls used by GeoPedia town quizzes.
 *
 * Town quizzes currently expose:
 *
 * - A Settings panel toggle.
 * - A Filter panel toggle.
 * - A warning when Filter cannot be opened during an active quiz.
 * - The currently open Settings and Filter panel contents.
 *
 * This component owns presentation only. The hydrated town quiz client remains
 * responsible for panel state, determining when Filter interactions are
 * blocked, controlling the blocked warning, and supplying the rendered panel
 * contents.
 *
 * Shared panel-toggle styling, Settings icon presentation, and blocked-panel
 * warning presentation are delegated to reusable quiz control components.
 */

"use client";

import type { ReactNode } from "react";

import QuizBlockedPanelMessage from "../shared/QuizBlockedPanelMessage";
import QuizSettingsIcon from "../shared/QuizSettingsIcon";
import QuizTogglePanelButton from "../shared/QuizTogglePanelButton";

/**
 * Props required by the floating town quiz panel controls.
 */
type TownQuizPanelControlsProps = {
  /** Whether the Settings panel is currently open. */
  isSettingsOpen: boolean;

  /** Whether the Filter panel is currently open. */
  isFilterOpen: boolean;

  /** Whether the warning explaining why Filter is unavailable is visible. */
  isFilterBlockedMessageOpen: boolean;

  /** Opens or closes the Settings panel. */
  onToggleSettings: () => void;

  /**
   * Attempts to open or close the Filter panel.
   *
   * The parent town quiz client determines whether this action is currently
   * allowed and may show the blocked warning instead.
   */
  onToggleFilter: () => void;

  /** Closes the warning explaining why Filter is unavailable. */
  onCloseFilterBlockedMessage: () => void;

  /** Rendered Settings panel content. */
  settingsPanel: ReactNode;

  /** Rendered Filter panel content. */
  filterPanel: ReactNode;
};

/**
 * Renders the floating town quiz panel toggles, blocked Filter warning, and
 * currently open auxiliary panels.
 *
 * @param props - Town panel state, callbacks, and rendered panel contents.
 * @returns Floating town quiz panel controls.
 */
export default function TownQuizPanelControls({
  isSettingsOpen,
  isFilterOpen,
  isFilterBlockedMessageOpen,
  onToggleSettings,
  onToggleFilter,
  onCloseFilterBlockedMessage,
  settingsPanel,
  filterPanel,
}: TownQuizPanelControlsProps) {
  return (
    <div className="absolute right-3 top-3 z-30 flex max-w-[calc(100vw-1.5rem)] flex-col items-end gap-5">
      {/* Floating panel toggle controls */}
      <div className="relative z-30 flex max-w-full flex-row items-start gap-5">
        {/* Settings panel toggle */}
        <QuizTogglePanelButton
          label="Quiz settings"
          isOpen={isSettingsOpen}
          onClick={onToggleSettings}
        >
          <QuizSettingsIcon />
        </QuizTogglePanelButton>

        {/* Filter panel toggle */}
        <QuizTogglePanelButton
          label="Quiz filter"
          isOpen={isFilterOpen}
          onClick={onToggleFilter}
        >
          Filter
        </QuizTogglePanelButton>

        {/* Warning displayed when Filter cannot be opened during a quiz */}
        {isFilterBlockedMessageOpen && (
          <QuizBlockedPanelMessage
            message="Finish or end the current quiz before filtering the quiz questions."
            onClose={onCloseFilterBlockedMessage}
          />
        )}
      </div>

      {/* Currently open auxiliary panels */}
      <div className="relative z-30 flex flex-row items-start gap-5">
        {/* Quiz Settings panel */}
        {isSettingsOpen && (
          <div className="mt-2">{settingsPanel}</div>
        )}

        {/* Town Filter panel */}
        {isFilterOpen && <div className="mt-2">{filterPanel}</div>}
      </div>
    </div>
  );
}
