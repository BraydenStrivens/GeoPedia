/**
 * Displays a temporary warning when an auxiliary quiz panel cannot currently
 * be opened.
 *
 * Feature and town quizzes both prevent certain panel interactions while a
 * quiz is running. For example, feature quizzes can block the Groups panel and
 * town quizzes can block the Filter panel. Those warnings share the same
 * positioning, appearance, accessibility behavior, dismissal behavior, and
 * close control.
 *
 * The warning automatically dismisses after a short delay while still allowing
 * the user to close it immediately. The parent owns visibility and quiz state;
 * this component only determines when dismissal should be requested.
 */

"use client";

import { useEffect } from "react";

/**
 * Time in milliseconds before a blocked-panel warning automatically dismisses.
 */
const AUTO_DISMISS_DELAY_MS = 3000;

/**
 * Props required by a blocked-panel warning.
 */
type QuizBlockedPanelMessageProps = {
  /** Explanation displayed to the user when the panel cannot be opened. */
  message: string;

  /** Accessible description for the warning's close button. */
  closeLabel?: string;

  /** Function called when the warning should be dismissed. */
  onClose: () => void;
};

/**
 * Renders a temporary warning for a currently unavailable quiz panel.
 *
 * The warning automatically requests dismissal after three seconds. Its close
 * button remains available for users who want to dismiss the message sooner.
 *
 * @param props - Warning text, close-button label, and dismissal callback.
 * @returns Floating blocked-panel warning.
 */
export default function QuizBlockedPanelMessage({
  message,
  closeLabel = "Close message",
  onClose,
}: QuizBlockedPanelMessageProps) {
  /**
   * Automatically dismisses the warning after the configured delay.
   *
   * The timeout is cleared when the component unmounts or when the dismissal
   * callback changes so a stale timer cannot trigger after the warning has
   * already been removed.
   */
  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      onClose();
    }, AUTO_DISMISS_DELAY_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [onClose]);

  return (
    <div
      className="
        absolute right-0 top-12 w-56
        rounded-lg border border-border
        bg-surface p-3
        text-xs text-text-secondary
        shadow-lg
      "
    >
      <div className="flex items-start gap-2">
        {/* Panel unavailable explanation */}
        <p className="flex-1 leading-relaxed">{message}</p>

        {/* Warning dismissal control */}
        <button
          type="button"
          onClick={onClose}
          aria-label={closeLabel}
          className="
            flex h-5 w-5 shrink-0 items-center justify-center
            rounded text-sm font-bold text-text-secondary
            transition-colors
            hover:bg-brand-soft hover:text-brand
            focus-visible:outline-none focus-visible:ring-2
            focus-visible:ring-focus
          "
        >
          ×
        </button>
      </div>
    </div>
  );
}
