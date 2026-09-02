/**
 * Displays GeoPedia's floating quiz Settings and Groups controls for feature quizzes.
 *
 * This component owns presentation only. The quiz client remains responsible
 * for deciding whether panels are open, whether Groups may be opened, and how
 * panel contents modify quiz state.
 */

"use client";

import type { ReactNode } from "react";

import QuizPanelButton from "../QuizPanelButton";

/**
 * Props required by the floating quiz-panel controls.
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

  /** Attempts to open or close the Groups panel. */
  onToggleGroups: () => void;

  /** Closes the Groups unavailable warning. */
  onCloseGroupsBlockedMessage: () => void;

  /** Rendered Settings panel content. */
  settingsPanel: ReactNode;

  /** Rendered Groups panel content. */
  groupsPanel: ReactNode;
};

/**
 * Displays floating panel buttons, the Groups warning, and any currently open
 * quiz panels.
 *
 * @param props - Panel state, callbacks, and rendered panel content.
 * @returns Floating quiz-panel controls.
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
      {/* Panel toggle buttons */}
      <div className="relative z-30 flex max-w-full flex-row items-start gap-5">
        {/* Settings panel toggle */}
        <QuizPanelButton
          label="Quiz settings"
          isOpen={isSettingsOpen}
          onClick={onToggleSettings}
        >
          {/* Settings gear icon */}
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            className="h-5 w-5"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.592c.55 0 1.02.398 1.11.94l.213 1.279c.063.379.313.696.645.889.09.052.18.107.268.164.325.21.72.275 1.082.139l1.223-.46a1.125 1.125 0 0 1 1.37.49l1.296 2.244a1.125 1.125 0 0 1-.26 1.431l-1.003.827a1.125 1.125 0 0 0-.38.95v.31c0 .374.137.735.38.95l1.003.827c.424.35.534.956.26 1.431l-1.296 2.244a1.125 1.125 0 0 1-1.37.49l-1.223-.46a1.125 1.125 0 0 0-1.082.139c-.088.057-.178.112-.268.164a1.125 1.125 0 0 0-.645.889l-.213 1.279c-.09.542-.56.94-1.11.94h-2.592c-.55 0-1.02-.398-1.11-.94l-.213-1.279a1.125 1.125 0 0 0-.645-.889 8.09 8.09 0 0 1-.268-.164 1.125 1.125 0 0 0-1.082-.139l-1.223.46a1.125 1.125 0 0 1-1.37-.49L3.447 15.3a1.125 1.125 0 0 1 .26-1.431l1.003-.827c.243-.2.38-.576.38-.95v-.31c0-.374-.137-.735-.38-.95l-1.003-.827a1.125 1.125 0 0 1-.26-1.431L4.743 6.33a1.125 1.125 0 0 1 1.37-.49l1.223.46c.362.136.757.071 1.082-.139.088-.057.178-.112.268-.164a1.125 1.125 0 0 0 .645-.889l.213-1.279Z"
            />

            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
            />
          </svg>
        </QuizPanelButton>

        {/* Groups panel toggle */}
        <QuizPanelButton
          label="Quiz groups"
          isOpen={isGroupsOpen}
          onClick={onToggleGroups}
        >
          Groups
        </QuizPanelButton>

        {/* Running-quiz Groups warning */}
        {isGroupsBlockedMessageOpen && (
          <div className="absolute right-0 top-12 w-56 rounded-lg border border-gray-300 bg-white p-3 text-xs text-gray-700 shadow-lg">
            <div className="flex items-start gap-2">
              {/* Warning message */}
              <p className="flex-1 leading-relaxed">
                Finish or end the current quiz before using Groups.
              </p>

              {/* Close warning */}
              <button
                type="button"
                onClick={onCloseGroupsBlockedMessage}
                aria-label="Close message"
                className="shrink-0 text-sm font-bold text-gray-400 transition hover:text-gray-900"
              >
                ×
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Floating panels */}
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
