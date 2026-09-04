/**
 * Displays a dismissible warning when an auxiliary quiz panel cannot currently
 * be opened.
 *
 * Feature and town quizzes both prevent certain panel interactions while a
 * quiz is running. For example, feature quizzes can block the Groups panel and
 * town quizzes can block the Filter panel. Those warnings share the same
 * positioning, appearance, accessibility behavior, and close control.
 *
 * This component centralizes that shared presentation while allowing each quiz
 * type to supply its own warning message. It owns no visibility or quiz state;
 * the parent decides when the warning should be rendered and handles dismissal.
 */

"use client";

/**
 * Props required by a blocked-panel warning.
 */
type QuizBlockedPanelMessageProps = {
  /** Explanation displayed to the user when the panel cannot be opened. */
  message: string;

  /** Accessible description for the warning's close button. */
  closeLabel?: string;

  /** Function called when the user dismisses the warning. */
  onClose: () => void;
};

/**
 * Renders a shared dismissible warning for a temporarily unavailable quiz
 * panel.
 *
 * @param props - Warning text, close-button label, and dismissal callback.
 * @returns Floating blocked-panel warning.
 */
export default function QuizBlockedPanelMessage({
  message,
  closeLabel = "Close message",
  onClose,
}: QuizBlockedPanelMessageProps) {
  return (
    <div className="absolute right-0 top-12 w-56 rounded-lg border border-border bg-background-1 p-3 text-xs text-text-secondary shadow-lg">
      <div className="flex items-start gap-2">
        {/* Panel unavailable explanation */}
        <p className="flex-1 leading-relaxed">{message}</p>

        {/* Warning dismissal control */}
        <button
          type="button"
          onClick={onClose}
          aria-label={closeLabel}
          className="shrink-0 text-sm font-bold text-text-secondary transition hover:text-text"
        >
          ×
        </button>
      </div>
    </div>
  );
}
