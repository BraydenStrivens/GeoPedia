/**
 * Displays a compact icon-based control used by GeoPedia quiz overlays.
 *
 * Feature and town quizzes use these controls for lifecycle actions such as
 * Skip, Stop, and Restart. Shared sizing, interaction behavior, accessibility,
 * and visual styling are centralized here so those controls remain consistent
 * across quiz types.
 *
 * The component owns no quiz state. Its parent supplies the accessible label,
 * icon content, and action callback.
 */

"use client";

import type { ReactNode } from "react";

/**
 * Props required by a compact quiz control button.
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
 * Displays a consistently styled compact quiz lifecycle control.
 *
 * The control uses a translucent neutral surface so it remains lightweight over
 * the map, with GeoPedia's blue brand colors reserved for hover and focus
 * emphasis. The existing pressed-scale interaction is preserved.
 *
 * @param props - Accessible label, icon content, and click callback.
 * @returns Compact icon-based quiz control button.
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
        "rounded-md border border-border bg-surface/80 text-text-secondary shadow-sm backdrop-blur-sm",
        "transition-colors hover:border-border-hover hover:bg-brand-soft hover:text-text active:scale-90",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
