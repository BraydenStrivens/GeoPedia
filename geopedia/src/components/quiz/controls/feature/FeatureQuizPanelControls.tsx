/**
 * Displays the floating auxiliary panel controls used by GeoPedia feature
 * quizzes.
 *
 * Feature quizzes currently expose:
 *
 * - A Settings panel toggle.
 * - A Groups panel toggle.
 * - A warning when Groups cannot be opened during an active quiz.
 * - The currently open Settings and Groups panel contents.
 *
 * This component owns presentation only. The hydrated feature quiz client
 * remains responsible for panel state, determining when Groups interactions
 * are blocked, controlling the blocked warning, and supplying the rendered
 * panel contents.
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
 * Props required by the floating feature quiz panel controls.
 */
type FeatureQuizPanelControlsProps = {
  /** Whether the Settings panel is currently open. */
  isSettingsOpen: boolean;

  /** Whether the Groups panel is currently open. */
  isGroupsOpen: boolean;

  /** Whether the warning explaining why Groups is unavailable is visible. */
  isGroupsBlockedMessageOpen: boolean;

  /** Opens or closes the Settings panel. */
  onToggleSettings: () => void;

  /**
   * Attempts to open or close the Groups panel.
   *
   * The parent feature quiz client determines whether this action is currently
   * allowed and may show the blocked warning instead.
   */
  onToggleGroups: () => void;

  /** Closes the warning explaining why Groups is unavailable. */
  onCloseGroupsBlockedMessage: () => void;

  /** Rendered Settings panel content. */
  settingsPanel: ReactNode;

  /** Rendered Groups panel content. */
  groupsPanel: ReactNode;
};

/**
 * Renders the floating feature quiz panel toggles, blocked Groups warning, and
 * currently open auxiliary panels.
 *
 * @param props - Feature panel state, callbacks, and rendered panel contents.
 * @returns Floating feature quiz panel controls.
 */
export default function FeatureQuizPanelControls({
  isSettingsOpen,
  isGroupsOpen,
  isGroupsBlockedMessageOpen,
  onToggleSettings,
  onToggleGroups,
  onCloseGroupsBlockedMessage,
  settingsPanel,
  groupsPanel,
}: FeatureQuizPanelControlsProps) {
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

        {/* Groups panel toggle */}
        <QuizTogglePanelButton
          label="Quiz groups"
          isOpen={isGroupsOpen}
          onClick={onToggleGroups}
        >
          Groups
        </QuizTogglePanelButton>

        {/* Warning displayed when Groups cannot be opened during a quiz */}
        {isGroupsBlockedMessageOpen && (
          <QuizBlockedPanelMessage
            message="Finish or end the current quiz before using feature groups."
            onClose={onCloseGroupsBlockedMessage}
          />
        )}
      </div>

      {/* Currently open auxiliary panels */}
      <div className="relative z-30 flex flex-row items-start gap-5">
        {/* Quiz Settings panel */}
        {isSettingsOpen && (
          <div className="mt-2">{settingsPanel}</div>
        )}

        {/* Quiz Groups panel */}
        {isGroupsOpen && <div className="mt-2">{groupsPanel}</div>}
      </div>
    </div>
  );
}
