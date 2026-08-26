/**
 * Displays a floating button used to toggle one of the quiz's auxiliary
 * panels.
 *
 * Settings and Groups use the same visual treatment, so this component keeps
 * their interaction styling consistent while allowing each control to provide
 * its own content.
 */

"use client";

import type { ReactNode } from "react";

/**
 * Props required by a floating quiz-panel toggle button.
 */
type QuizPanelButtonProps = {
  /** Accessible name describing the panel controlled by the button. */
  label: string;

  /** Whether the associated panel is currently open. */
  isOpen: boolean;

  /** Opens or closes the associated panel. */
  onClick: () => void;

  /** Visible button content, such as text or an icon. */
  children: ReactNode;
};

/**
 * Displays a shared floating quiz-panel toggle button.
 *
 * @param props - Panel state, accessible label, content, and toggle callback.
 * @returns A floating quiz-panel button.
 */
export default function QuizPanelButton({
  label,
  isOpen,
  onClick,
  children,
}: QuizPanelButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      aria-expanded={isOpen}
      className={[
        "flex h-10 items-center justify-center rounded-lg border border-white p-3",
        "shadow-sm backdrop-blur-md",
        "text-gray-900 transition-all duration-200",

        isOpen
          ? "bg-white hover:bg-white/50"
          : "bg-white/30 hover:bg-white/70",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
