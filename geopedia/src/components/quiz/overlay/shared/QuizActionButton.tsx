/**
 * Displays a large text action available while a quiz is inactive.
 *
 * Feature and town quiz overlays use this component for prominent actions such
 * as Start and Show Answers. Shared styling and disabled behavior are
 * centralized here so those actions remain visually consistent across quiz
 * types.
 *
 * The component owns no quiz state. Its parent controls availability and
 * supplies the action callback.
 */

"use client";

import type { ReactNode } from "react";

/**
 * Props required by an inactive quiz action button.
 */
type QuizActionButtonProps = {
  /** Text or other content displayed inside the button. */
  children: ReactNode;

  /** Whether the action is temporarily unavailable. */
  isDisabled?: boolean;

  /** Optional browser tooltip displayed while hovering the button. */
  title?: string;

  /** Function called when the button is selected. */
  onClick: () => void;
};

/**
 * Displays a consistently styled inactive quiz action.
 *
 * Enabled buttons use GeoPedia's primary button colors because these controls
 * represent prominent quiz actions such as starting a quiz or showing answers.
 * Disabled buttons use the global disabled-state colors and prevent interaction.
 *
 * @param props - Button content, disabled state, tooltip, and callback.
 * @returns Large quiz action button.
 */
export default function QuizActionButton({
  children,
  isDisabled = false,
  title,
  onClick,
}: QuizActionButtonProps) {
  return (
    <button
      type="button"
      disabled={isDisabled}
      title={title}
      onClick={onClick}
      className={[
        "rounded-lg border px-5 py-1.5 text-center text-lg font-bold leading-tight",
        "backdrop-blur-md transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus",
        isDisabled
          ? "cursor-not-allowed border-border bg-disabled text-disabled-text"
          : "border-brand bg-button text-button-text hover:border-brand-hover-strong hover:bg-button-hover",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
