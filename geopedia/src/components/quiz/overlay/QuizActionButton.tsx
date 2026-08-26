/**
 * Displays a large text action available while a quiz is inactive.
 *
 * Start and Show Answers use the same visual treatment and disabled behavior,
 * so this component keeps those actions visually consistent.
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
        "rounded-lg px-5 py-1.5 text-center text-lg font-bold leading-tight",
        "backdrop-blur-md transition",

        isDisabled
          ? "cursor-not-allowed bg-gray-300 text-gray-500"
          : "bg-white/80 text-gray-900 hover:bg-gray-300",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
