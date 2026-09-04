/**
 * Displays a reusable boolean setting row for GeoPedia quiz settings panels.
 *
 * Each row contains a setting label, optional contextual help control, and
 * compact boolean toggle. Feature and town settings panels share this
 * presentation so quiz settings remain visually and behaviorally consistent.
 *
 * The boolean setting value is owned by the parent component. Contextual-help
 * visibility is local presentation state owned by this component.
 */

"use client";

import { useState } from "react";

/**
 * Props required by a reusable quiz settings toggle row.
 */
type QuizSettingsToggleRowProps = {
  /** User-facing setting name. */
  label: string;

  /** Whether the boolean setting is currently enabled. */
  isEnabled: boolean;

  /**
   * Optional explanation displayed through the contextual help control.
   *
   * When omitted, no help button is displayed.
   */
  description?: string;

  /** Called when the user toggles the boolean setting. */
  onToggle: () => void;
};

/**
 * Displays a boolean quiz setting with optional contextual help.
 *
 * @param props - Toggle-row properties.
 * @param props.label - User-facing setting name.
 * @param props.isEnabled - Current boolean setting value.
 * @param props.description - Optional contextual help description.
 * @param props.onToggle - Callback for changing the setting value.
 * @returns The reusable quiz settings toggle row.
 */
export default function QuizSettingsToggleRow({
  label,
  isEnabled,
  description,
  onToggle,
}: QuizSettingsToggleRowProps) {
  /**
   * Whether this setting's contextual help description is currently visible.
   */
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  return (
    <div className="relative">
      {/* Setting row */}
      <div className="flex items-center justify-between gap-4">
        {/* Setting label and optional help button */}
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-medium text-text">
            {label}
          </span>

          {description && (
            <button
              type="button"
              onClick={() =>
                setIsHelpOpen((currentValue) => !currentValue)
              }
              aria-label={`About ${label}`}
              aria-expanded={isHelpOpen}
              className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-border text-[10px] font-bold leading-none text-text-secondary transition hover:border-border-hover hover:text-text"
            >
              ?
            </button>
          )}
        </div>

        {/* Boolean setting toggle */}
        <button
          type="button"
          onClick={onToggle}
          aria-label={`Toggle ${label}`}
          aria-pressed={isEnabled}
          className="shrink-0"
        >
          <span
            className={[
              "block h-4 w-4 rounded-full border-2 transition",
              isEnabled
                ? "border-selected-control bg-selected-control hover:bg-selected-control-hover"
                : "border-border bg-transparent hover:border-border-hover",
            ].join(" ")}
          />
        </button>
      </div>

      {/* Optional contextual help description */}
      {description && isHelpOpen && (
        <div
          className="mt-2 rounded-lg border border-border bg-background-1 p-2.5 text-xs leading-relaxed text-text-secondary shadow-sm"
          role="note"
        >
          {description}
        </div>
      )}
    </div>
  );
}
