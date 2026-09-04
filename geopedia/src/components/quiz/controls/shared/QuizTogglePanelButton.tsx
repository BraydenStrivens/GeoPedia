/**
 * Displays a floating button used to toggle one of GeoPedia's auxiliary quiz
 * panels.
 *
 * Feature and town quiz controls can reuse this component for panel toggles
 * such as Settings, Groups, or other floating quiz tools. Shared sizing,
 * accessibility, transition behavior, and visual styling are centralized here
 * so panel controls remain consistent across quiz types.
 *
 * The button reflects whether its associated panel is currently open, but it
 * owns no panel state. The parent component supplies both the open state and
 * the toggle callback.
 */

"use client";

import type { ReactNode } from "react";

/**
 * Props required by a floating quiz-panel toggle button.
 */
type QuizTogglePanelButtonProps = {
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
 * Open and closed states use different background opacity while inheriting
 * GeoPedia's shared border and text colors from the global semantic style
 * system.
 *
 * @param props - Panel state, accessible label, content, and toggle callback.
 * @returns Floating button controlling an auxiliary quiz panel.
 */
export default function QuizTogglePanelButton({
  label,
  isOpen,
  onClick,
  children,
}: QuizTogglePanelButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      aria-expanded={isOpen}
      className={[
        "flex h-10 items-center justify-center rounded-lg border border-background-1 p-3",
        "shadow-sm backdrop-blur-md",
        "text-text transition-all duration-200",
        isOpen
          ? "bg-background-1 hover:bg-background-1/50"
          : "bg-background-1/30 hover:bg-background-1/70",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
