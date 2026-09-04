/**
 * Provides the shared floating layout used by GeoPedia quiz overlays.
 *
 * Both feature and town quizzes display their primary quiz information inside
 * a translucent panel positioned above the map, with lifecycle controls
 * rendered directly beneath that panel.
 *
 * This component owns only the shared physical overlay structure. Quiz-specific
 * information, scoring, questions, results, and control behavior remain owned
 * by the feature or town overlay that renders inside it.
 */

"use client";

import type { ReactNode } from "react";

/**
 * Props required by the shared quiz overlay shell.
 */
type QuizOverlayShellProps = {
  /**
   * Tailwind minimum-width class applied to the main information panel.
   *
   * Feature and town overlays currently use slightly different minimum widths
   * because their quiz information requires different amounts of horizontal
   * space.
   */
  minWidthClassName: string;

  /** Quiz-specific information rendered inside the main overlay panel. */
  children: ReactNode;

  /**
   * Optional lifecycle controls rendered beneath the main information panel.
   *
   * When omitted, the lower controls row is not rendered.
   */
  controls?: ReactNode;
};

/**
 * Renders the common floating container used by GeoPedia quiz overlays.
 *
 * The outer element ignores pointer events so the map remains interactive
 * around the overlay. The information panel restores pointer events for its
 * interactive controls.
 *
 * @param props - Overlay content, minimum width, and optional lower controls.
 * @returns Shared floating quiz overlay structure.
 */
export default function QuizOverlayShell({
  minWidthClassName,
  children,
  controls,
}: QuizOverlayShellProps) {
  return (
    <div className="pointer-events-none absolute inset-x-0 top-3 z-10 flex flex-col items-center">
      {/* Main translucent quiz information panel */}
      <div
        className={[
          "pointer-events-auto rounded-xl bg-black/20 p-2 backdrop-blur-sm",
          minWidthClassName,
        ].join(" ")}
      >
        {children}
      </div>

      {/* Optional quiz lifecycle controls beneath the main panel */}
      {controls && (
        <div className="mt-1 flex justify-center gap-1">
          {controls}
        </div>
      )}
    </div>
  );
}
