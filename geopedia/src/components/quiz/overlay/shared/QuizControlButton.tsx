/**
 * Displays a compact icon-based control used while a quiz is active.
 *
 * Skip, Stop, and Restart share the same interaction styling, so this
 * component centralizes that appearance.
 */

"use client";

import type { ReactNode } from "react";

/**
 * Props required by an active quiz control button.
 */
type QuizControlButtonProps = {
  /** Accessible description and browser tooltip for the control. */
  title: string;

  /** Icon displayed inside the button. */
  children: ReactNode;

  /** Function called when the control is selected. */
  onClick: () => void;
};

/**
 * Displays a consistently styled compact quiz control.
 *
 * @param props - Tooltip, icon content, and click callback.
 * @returns Compact active-quiz control button.
 */
export default function QuizControlButton({
  title,
  children,
  onClick,
}: QuizControlButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      aria-label={title}
      className={[
        "pointer-events-auto flex h-6 w-6 items-center justify-center",
        "rounded-md bg-white/80 text-gray-600 shadow-sm backdrop-blur-sm",
        "transition hover:bg-gray-300 hover:text-black active:scale-90",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
